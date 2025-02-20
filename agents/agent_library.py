from typing import List, TypedDict, Optional

from agents.agent_tool import DataTools

class AgentConfig(TypedDict):
    tools: List
    prompt: Optional[str]


agent_configs: dict[str, AgentConfig] = {
    "data_team": {
        "tools": [DataTools.get_tavily_search_tool(),
                  DataTools.get_stock_news()],
        "prompt": """\n
                    You are an intelligent news collection agent designed to retrieve and summarize the latest news from reliable sources. \n
                    Your primary goal is to gather up-to-date and relevant news articles based on specific topics, keywords, or categories\n
                """
    },
    "financial_team": {
        "tools": [],
        "prompt": ""
    },
    "reporter_team": {
        "tools": [],
        "prompt": ""
    },
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