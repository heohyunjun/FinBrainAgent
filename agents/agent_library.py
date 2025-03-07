from agents.agent_tool import DataTools, DataCleansingTools, ReportTools, InvestmentTools
from typing import TypedDict, List, Annotated, Literal, Dict, Callable, TypeVar, Tuple, Type, Generic, Optional, Any

class AgentConfig(TypedDict):
    tools: List
    prompt: Optional[str]

agent_configs: dict[str, AgentConfig] = {
    "team_director": {
        "tools": [],
        "prompt": """
            You are a director managing a conversation between the following teams: {team_node_list}.
            
            Instructions:
            1. Given the user request, respond with the team to act next.
            2. Each team will perform a task and return results.
            3. When finished, respond with FINISH.
            
            Team Assignment Guidelines:
                - If data collection is required, assign the task to the data_team.
                - If financial analysis is needed, assign the task to the financial_team.
                - If report writing is necessary, assign the task to the reporter_team.
        """
    },
    "data_team": {
        "tools": [],
        "prompt": """
            You are a director managing a conversation between the following workers: {data_agent_node_list}.
            
            Instructions:
            1. Given the user request, determine and respond with the worker to act next.
            2. Each worker will perform a task and return results.
            3. Ensure that data collection is followed by a data cleaning process before proceeding to further steps.
            4. Evaluate the results from each worker and decide if additional actions are needed or if the task is complete.
            5. When all tasks (including data collection and cleaning) are finished and the request is fully addressed, respond with FINISH.
        """
    },
    "financial_team": {
        "tools": [],
        "prompt": """
            You are a director managing a conversation between the following workers: {financial_agent_node_list}.
            
            Instructions:
            1. Given the user request, respond with the worker to act next.
            2. Each worker will perform a task and return results.
            3. When finished, respond with FINISH.
        """
    },
    "reporter_team": {
        "tools": [],
        "prompt": """
            You are a director managing a conversation between the following workers: {reporter_agent_node_list}.
            
            Instructions:
            1. Given the user request, respond with the worker to act next.
            2. Each worker will perform a task and return results.
            3. When finished, respond with FINISH.
        """
    },
    "data_retrieval": {
        "tools": [DataTools.get_tavily_search_tool, DataTools.get_stock_news],
        "prompt": ("""
                "Your role is a financial data retrieval expert. "
                "Collect the data required for the user's request."
                "You can use the following tools: get_tavily_search_tool and get_stock_news. "
                "Use only the tools necessary to collect relevant financial data. "
                "Once data collection is complete, end your task. "
                "When the task is finished, respond with your output in this format: - output: "
                "If you are unable to fully answer, that's OK."
            """
        )
    },
    "data_cleaning": {
        "tools": [
            DataCleansingTools.remove_duplicates,
            DataCleansingTools.standardize_dates,
            DataCleansingTools.normalize_numbers,
            DataCleansingTools.handle_missing,
            DataCleansingTools.detect_outliers
        ],
        "prompt": """

        """
    },
    "news_sentiment": {
        "tools": [
            DataTools.get_stock_news,
            DataTools.get_tavily_search_tool
        ],
        "prompt": """
        """
    },
    "market_trend": {
        "tools": [
            DataTools.get_core_cpi_data,
            DataTools.get_core_pce_data,
            DataTools.get_unemployment_rate_data
        ],
        "prompt": """

        """
    },
    "investment_strategy": {
        "tools": [
            InvestmentTools.analyze_risk_reward,
            InvestmentTools.generate_asset_allocation,
            InvestmentTools.create_investment_timeline
        ],
        "prompt": """
        """
    },
    "report_generation": {
        "tools": [
            ReportTools.generate_report_structure,
            ReportTools.format_report_section
        ],
        "prompt": """
        """
    },
    "summary_extraction": {
        "tools": [
            ReportTools.extract_key_points,
            ReportTools.generate_executive_summary
        ],
        "prompt": """
        """
    }
}