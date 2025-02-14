from typing import List, TypedDict, Optional


class AgentConfig(TypedDict):
    tools: List
    prompt: Optional[str]


agent_configs: dict[str, AgentConfig] = {
    "data_retrieval": {
        "tools": [],
        "prompt": ""
    },
    "data_cleaning": {
        "tools": [],
        "prompt": ""
    },
    "news_sentiment": {
        "tools": [],
        "prompt": ""
    },
    "market_trend": {
        "tools": [],
        "prompt": ""
    },
    "investment_strategy": {
        "tools": [],
        "prompt": ""
    },
    "report_generation": {
        "tools": [],
        "prompt": ""
    },
    "summary_extraction": {
        "tools": [],
        "prompt": ""
    }
}