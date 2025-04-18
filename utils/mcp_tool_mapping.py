def bind_agent_tools(agent_configs, mcp_tools):
    bound_configs = {}
    mcp_tool_map = {tool.name: tool for tool in mcp_tools or []}

    for agent_name, cfg in agent_configs.items():
        resolved = cfg.copy()
        resolved_tools = []

        for tool in cfg.get("tools", []):
            if isinstance(tool, dict) and "mcp" in tool:
                tool_name = tool["mcp"]
                fallback = tool.get("fallback")
                if tool_name in mcp_tool_map:
                    resolved_tools.append(mcp_tool_map[tool_name])
                else:
                    print(f"[WARN] MCP 툴 '{tool_name}' 누락 → fallback 적용 (agent: {agent_name})")
                    if fallback:
                        resolved_tools.append(fallback)
                    else:
                        print(f"[WARN] fallback도 없어 tool '{tool_name}' 무시됨.")
            # 문자열 MCP 툴 참조 
            elif isinstance(tool, str) and tool.startswith("mcp:"):
                tool_name = tool.replace("mcp:", "")
                if tool_name in mcp_tool_map:
                    resolved_tools.append(mcp_tool_map[tool_name])
                else:
                    print(f"[WARN] MCP 툴 '{tool_name}' 누락 → 원본 문자열 유지 (agent: {agent_name})")
                    resolved_tools.append(tool)
            else:
                resolved_tools.append(tool)

        resolved["tools"] = resolved_tools
        bound_configs[agent_name] = resolved

    return bound_configs
