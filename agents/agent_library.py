from agents.agent_tool import DataTools, DataCleansingTools
from typing import TypedDict, List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic, Optional, Any

class AgentConfig(TypedDict):
    tools: List
    prompt: Optional[str]

agent_configs: dict[str, AgentConfig] = {
    "data_team": {
        "tools": [

        ],
        "prompt": ""
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
        "tools": [            
            DataTools.get_tavily_search_tool(),
            DataTools.get_stock_news],
        "prompt": """\n
                You are an intelligent news collection agent designed to retrieve and summarize the latest news from reliable sources. \n
                Your primary goal is to gather up-to-date and relevant news articles based on specific topics, keywords, or categories\n
            """
    },
    "data_cleaning": {
        "tools": [
            DataCleansingTools.remove_duplicates,
            DataCleansingTools.standardize_dates,
            DataCleansingTools.normalize_numbers,
            DataCleansingTools.handle_missing,
            DataCleansingTools.detect_outliers
        ],
        "prompt": """You are a Data-Cleansing Agent for a financial expert AI service. Your task is to process raw financial data collected from various sources and prepare it for analysis. You have access to tools like `remove_duplicates`, `standardize_dates`, `normalize_numbers`, `handle_missing`, and `detect_outliers`.

            For each dataset received, follow these steps:
            1. Identify the data type (e.g., stock news as a list of strings, economic indicators as a list of dictionaries) based on its structure.
            2. Apply relevant cleansing tools:
               - For all datasets: Remove duplicates using `remove_duplicates` and standardize dates to YYYY-MM-DD using `standardize_dates` (default key: 'date').
               - For numeric data (e.g., CPI, PCE, income): Convert strings to floats using `normalize_numbers` and replace missing values (e.g., 'N/A', None) with defaults using `handle_missing`.
               - For outlier detection: Use `detect_outliers` on key numeric fields to flag anomalies (default threshold: 3 standard deviations).
               - For news (list of strings): Filter out irrelevant or redundant entries based on financial relevance.
            3. Use your judgment to:
               - Flag potential issues (e.g., inconsistent units, unexpected text in numeric fields).
               - Ensure news summaries are concise and finance-related.
            4. Return the cleansed data in its original format (List[Dict] or List[str]) along with a log of actions taken (e.g., "Removed 2 duplicates, normalized 5 numbers").

            Input: {input}
            Output format: { "cleansed_data": ..., "log": [...] }
        """
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