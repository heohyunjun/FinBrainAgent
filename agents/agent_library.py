from typing import TypedDict, List, Optional, Literal
from sec_tool.market_data_tool import MarketDataTools, FinancialDataTools, EconomicDataTools
from sec_tool.insider_trade_tool import SECInsiderTradeAPI,SEC13D13GAPI, SEC13FHoldingsAPI
from agents.prompt_utils import *
from dart_tool.dart_tool_registry import DartToolRegistry

dart_registry = DartToolRegistry()

class AgentConfig(TypedDict, total=False):
    tools: List
    prompt: Optional[str]
    agent_type: Literal["worker", "supervisor"]
    members: Optional[List[str]]  

agent_configs: dict[str, AgentConfig] = {
    "economic_data_retrieval_agent": {
        "tools": [EconomicDataTools.get_core_cpi_data],
        "prompt": get_economic_data_retrieval_prompt(),
        "agent_type": "worker"
    },
    "market_data_retrieval_agent": {
        "tools": [MarketDataTools.get_stock_price],
        "prompt": get_market_data_retrieval_prompt(),
        "agent_type": "worker"
    },
    "financial_statement_retrieval_agent": {
        "tools":  [
            FinancialDataTools.get_income_statement,
            FinancialDataTools.get_financial_event_filings
            ],
        "prompt": get_financial_statement_data_retrieval_prompt(),
        "agent_type": "worker"
    },
    "data_retrieval_leader_agent": {
        "tools": [],
        "prompt": get_data_retrieval_leader_system_prompt(),
        "agent_type": "supervisor",
        "members": [
            "news_and_sentiment_retrieval", "market_data_retrieval", 
            "financial_statement_retrieval","insider_team_leader",
            "economic_data_retrieval"
            ] 
    },
    "data_cleansing_agent": {
        "tools": [],
        "prompt": get_data_cleansing_system_prompt(),
        "agent_type": "worker"
    },
    "news_and_sentiment_retrieval_agent": {
        "tools": [MarketDataTools.get_stock_news, MarketDataTools.get_websearch_tool] ,
        "prompt": get_news_and_sentiment_retrieval_prompt(),
        "agent_type": "worker"
    },
    "supervisor": {
        "tools": [],
        "prompt": get_supervisor_system_prompt(),
        "agent_type": "supervisor",
        "members" : [
            "data_retrieval_leader", "general_team_leader"
            ]
    },
    "insider_team_leader": {
        "tools": [],
        "prompt": get_insider_tracker_research_leader_prompt(),
        "agent_type": "supervisor",
        "members" : ["domestic_insider_researcher","international_insider_researcher" ]
    },
    "domestic_insider_researcher": {
        "tools": [
            dart_registry.get_executive_shareholding_tool,
            dart_registry.get_major_stock_reports_tool,
            dart_registry.get_ts_disposal_tool,
            dart_registry.get_ts_acquisition_tool,
            dart_registry.get_ts_trust_contract_tool,
            dart_registry.get_ts_trust_cancel_tool,
        ],
        "prompt": get_domestic_insider_researcher_prompt(),
        "agent_type": "worker",
    },
    "international_insider_researcher": {
        "tools": [
            SECInsiderTradeAPI.fetch_filings_form3_4_5,
            SEC13D13GAPI.fetch_filings_form13d_13g,
            SEC13FHoldingsAPI.fetch_filings_13f  
        ],
        "prompt": get_international_insider_researcher_prompt(),
        "agent_type": "worker",
    }

}
