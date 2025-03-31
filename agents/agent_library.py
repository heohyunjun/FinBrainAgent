from typing import TypedDict, List, Optional, Literal
from sec_tool.market_data_tool import MarketDataTools, FinancialDataTools, EconomicDataTools
from sec_tool.insider_trade_tool import SECInsiderTradeAPI
from agents.prompt_utils import *



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
            FinancialDataTools.get_income_statement, FinancialDataTools.get_financial_event_filings
            ],
        "prompt": get_financial_statement_data_retrieval_prompt(),
        "agent_type": "worker"
    },
    "insider_tracker_research_agent": {
        "tools": [SECInsiderTradeAPI.fetch_filings],
        "prompt": get_insider_tracker_data_prompt(),
        "agent_type": "worker"
    },
    "data_retrieval_leader_agent": {
        "tools": [],
        "prompt": get_data_retrieval_leader_system_prompt(),
        "agent_type": "supervisor",
        "members": [
            "news_and_sentiment_retrieval", "market_data_retrieval", 
            "financial_statement_retrieval","insider_tracker_research",
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
        "prompt": get_news_and_sentiment_retrieval_prompt(),
        "agent_type": "supervisor",
        "members" : [
            "data_retrieval_leader", "general_team_leader"
            ]
    }
}
