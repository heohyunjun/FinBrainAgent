from typing import TypedDict, List, Optional

from agents.prompt_utils import *


class AgentConfig(TypedDict):
    tools: List
    prompt: Optional[str]

agent_configs: dict[str, AgentConfig] = {
    "economic_data_retrieval_agent": {
        "tools": [],
        "prompt": get_economic_data_prompt()
    },
    "market_data_retrieval_agent": {
        "tools": [],
        "prompt": get_market_data_prompt()
    },
    "financial_statement_retrieval_agent": {
        "tools": [],
        "prompt": get_financial_statement_data_prompt()
    },
    "insider_tracker_research_agent": {
        "tools": [],
        "prompt": get_insider_tracker_data_prompt()
    },
    "data_retrieval_leader_agent": {
        "tools": [],
        "prompt": get_data_retrieval_leader_system_prompt()
    },
    "data_cleansing_agent": {
        "tools": [],
        "prompt": data_cleansing_system_prompt()
    },
    "supervisor": {
        "tools": [],
        "prompt": supervisor_system_prompt()
    }
}