import os
import sys
import anyio
import asyncio
from contextlib import asynccontextmanager
from typing import Literal, TextIO, Any
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from anyio.streams.text import TextReceiveStream

import mcp.types as types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import _create_platform_compatible_process, get_default_environment
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.tools import BaseTool
from utils.logger import logger

class ManagedMCPServer:
    def __init__(self, name: str, session, process):
        self.name = name
        self.session = session
        self.process = process

    def is_alive(self) -> bool:
        if self.process:
            return self.process.returncode is None
        return True  # WebSocket은 따로 ping으로 확인

    async def ping(self) -> bool:
        try:
            await self.session.send_ping()
            return True
        except Exception:
            return False


class PatchedMultiServerMCPClient(MultiServerMCPClient):
    def __init__(self, connections: dict):
        super().__init__(connections)
        self.managed_sessions: dict[str, ManagedMCPServer] = {}

    async def connect_to_server_via_stdio_with_process(
        self,
        server_name: str,
        *,
        command: str,
        args: list[str],
        env: dict[str, str] | None = None,
        encoding: str = "utf-8",
        encoding_error_handler: str = "strict",
        session_kwargs: dict[str, Any] | None = None,
    ) -> None:
        env = env or {}
        if "PATH" not in env:
            env["PATH"] = os.environ.get("PATH", "")

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
            encoding=encoding,
            encoding_error_handler=encoding_error_handler,
        )

        stderr_log_path = os.path.join("logs", f"{server_name}_stderr.log")
        stderr_log_file = open(stderr_log_path, "a", encoding="utf-8")

        read, write, process = await self.exit_stack.enter_async_context(
            stdio_client_with_process(server_params, errlog=stderr_log_file)
        )

        session_kwargs = session_kwargs or {}
        session = await self.exit_stack.enter_async_context(
            ClientSession(read, write, **session_kwargs)
        )
        await session.initialize()

        self.managed_sessions[server_name] = ManagedMCPServer(
            name=server_name,
            session=session,
            process=process,
        )

        tools = await load_mcp_tools(session)
        self.server_name_to_tools[server_name] = tools

    async def connect_to_server(
        self,
        server_name: str,
        *,
        transport: Literal["stdio", "sse", "websocket"] = "stdio",
        **kwargs,
    ) -> None:
        if transport == "stdio":
            await self.connect_to_server_via_stdio_with_process(
                server_name,
                command=kwargs["command"],
                args=kwargs["args"],
                env=kwargs.get("env"),
                encoding=kwargs.get("encoding", "utf-8"),
                encoding_error_handler=kwargs.get("encoding_error_handler", "strict"),
                session_kwargs=kwargs.get("session_kwargs"),
            )
        else:
            await super().connect_to_server(server_name, transport=transport, **kwargs)


@asynccontextmanager
async def stdio_client_with_process(server: StdioServerParameters, errlog: TextIO = sys.stderr):
    read_stream_writer, read_stream = anyio.create_memory_object_stream(0)
    write_stream, write_stream_reader = anyio.create_memory_object_stream(0)

    process = await _create_platform_compatible_process(
        command=server.command,
        args=server.args,
        env={**get_default_environment(), **(server.env or {})},
        errlog=errlog,
        cwd=server.cwd,
    )

    async def stdout_reader():
        buffer = ""
        async with read_stream_writer:
            async for chunk in TextReceiveStream(
                process.stdout,
                encoding=server.encoding,
                errors=server.encoding_error_handler,
            ):
                lines = (buffer + chunk).split("\n")
                buffer = lines.pop()
                for line in lines:
                    try:
                        message = types.JSONRPCMessage.model_validate_json(line)
                        await read_stream_writer.send(message)
                    except Exception as exc:
                        logger.warning(f"[StdioClient] JSON decode 실패: '{line.strip()}' → {exc}")
                        await read_stream_writer.send(exc)

    async def stdin_writer():
        async with write_stream_reader:
            async for message in write_stream_reader:
                json = message.model_dump_json(by_alias=True, exclude_none=True)
                await process.stdin.send(
                    (json + "\n").encode(
                        encoding=server.encoding,
                        errors=server.encoding_error_handler,
                    )
                )

    async with (
        anyio.create_task_group() as tg,
        process,
    ):
        tg.start_soon(stdout_reader)
        tg.start_soon(stdin_writer)
        try:
            yield read_stream, write_stream, process
        finally:
            if sys.platform == "win32":
                from mcp.client.win32 import terminate_windows_process
                await terminate_windows_process(process)
            else:
                process.terminate()


async def mcp_watchdog(client: PatchedMultiServerMCPClient, interval: int = 30):
    logger.info("[Watchdog] 연결")
    while True:
        for name, config in client.connections.items():
            if name not in client.managed_sessions:
                logger.warning(f"[Watchdog] MCP '{name}' 세션 없음 → 연결 시도")
                await client.connect_to_server(name, **config)
                continue

            managed = client.managed_sessions[name]

            if managed.process and not managed.is_alive():
                logger.warning(f"[Watchdog] MCP '{name}' subprocess 죽음 → 재연결")
                try:
                    await client.connect_to_server(name, **config)
                    logger.info(f"[Watchdog] MCP '{name}' subprocess 재연결 완료")
                except Exception as e:
                    logger.error(f"[Watchdog] MCP '{name}' 재연결 실패: {e}")


            try:
                ok = await managed.ping()
                if not ok:
                    logger.warning(f"[Watchdog] MCP '{name}' ping 실패 → 재연결")
                    await client.connect_to_server(name, **config)
                    logger.info(f"[Watchdog] MCP '{name}' ping 기반 재연결 완료")
            except Exception as e:
                logger.warning(f"[Watchdog] MCP '{name}' ping 예외 발생: {e}")
                await client.connect_to_server(name, **config)
                logger.info(f"[Watchdog] MCP '{name}' 예외 기반 재연결 완료")


        await asyncio.sleep(interval)
