import json
from typing import Dict
from mcp_agent.config import MCPServerSettings
from mcp_agent.mcp_server_registry import ServerRegistry
from mcp_agent.config import MCPServerSettings

def load_mcp_server_settings(config_path: str) -> Dict[str, MCPServerSettings]:
    with open(config_path, "r", encoding="utf-8") as f:
        raw_config = json.load(f)

    servers = {}
    for name, server in raw_config["mcpServers"].items():
        settings = MCPServerSettings(
            name=name,
            transport=server["transport"],
            command=server.get("command"),
            args=server.get("args"),
            env=server.get("env"),
            url=server.get("url"),
            headers=server.get("headers"),
            read_timeout_seconds=30  # 기본값 설정 가능
        )
        servers[name] = settings

    return servers

def get_server_registry(config_path: str = "./mcp_config.json") -> ServerRegistry:
    mcp_servers = load_mcp_server_settings(config_path)

    registry = ServerRegistry()
    for name, setting in mcp_servers.items():
        registry.registry[name] = setting

    return registry