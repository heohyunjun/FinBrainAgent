import os
import uuid
import datetime
import logging
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, UnstructuredPDFLoader, PDFPlumberLoader

from langchain_openai import OpenAIEmbeddings, ChatOpenAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_core.documents import Document

import operator
from typing import Annotated, List, TypedDict, Literal, Optional
from langgraph.types import Send

from langgraph.graph import END, START, StateGraph
from langchain.chains.combine_documents.reduce import (
    acollapse_docs, split_list_of_docs,
)



from utils.logger import logger


token_max = 1000

class OverallState(TypedDict):
    contents: List[str]
    summaries: Annotated[list, operator.add]
    collapsed_summaries: List[Document]
    final_summary: str
    translated_summary: str

llm = ChatOpenAI(temperature=0, model_name="gpt-4o-mini-2024-07-18")

map_chain = ChatPromptTemplate.from_template("Write a concise summary of the following: {context}.") | llm | StrOutputParser()
reduce_chain = ChatPromptTemplate.from_template(
    "The following is a set of summaries:\n{docs}\nTake these and distill it into a final summary."
) | llm | StrOutputParser()

async def generate_summary_node(state: dict):
    logger.debug(f"Generating summary for content chunk...")
    response = await map_chain.ainvoke({"context": state["content"]})
    return {"summaries": [response]}


def collect_summaries_node(state: OverallState):
    logger.debug("Collecting summaries for potential collapsing...")
    return {"collapsed_summaries": [Document(page_content=summary) for summary in state["summaries"]]}

def length_function(documents: List[Document]) -> int: 
    return sum(llm.get_num_tokens(doc.page_content) for doc in documents)


async def collapse_summaries_node(state: OverallState):
    logger.info("Collapsing summaries as they exceed token_max...")
    collapsed_summaries = state["collapsed_summaries"]
    doc_lists = split_list_of_docs(collapsed_summaries, length_function, token_max)
    results = []
    for doc_list in doc_lists:
        collapsed_doc = await acollapse_docs(doc_list, reduce_chain.ainvoke)
        results.append(collapsed_doc)
    logger.info(f"Summaries collapsed into {len(results)} documents.")
    return {"collapsed_summaries": results}

async def generate_final_summary_node(state: OverallState):
    logger.info("Generating final summary...")
    response = await reduce_chain.ainvoke({"docs": state["collapsed_summaries"]})
    return {"final_summary": response}

def map_summaries_edge(state: OverallState):
    logger.debug("Mapping contents to summary nodes...")
    return [Send("generate_summary_node", {"content": content}) for content in state["contents"]]

def should_collapse_edge(state: OverallState) -> Literal["collapse_summaries_node", "generate_final_summary_node"]:
    num_tokens = length_function(state["collapsed_summaries"])
    logger.debug(f"Checking if summaries need collapsing. Current token count: {num_tokens}, Max: {token_max}")
    if num_tokens > token_max: 
        logger.info("Summaries exceed token limit, collapsing further.")
        return "collapse_summaries_node"
    else: 
        logger.info("Summaries within token limit, generating final summary.")
        return "generate_final_summary_node"


async def translate_to_korean_node(state: OverallState):
    logger.info("Translating final summary to Korean...")

    final_summary = state.get("final_summary")
    if not final_summary:
        logger.warning("No final summary found. Skipping translation.")
        return {"translated_summary": None}

    # 번역 프롬프트
    translate_template = (
        "Please translate the following text into **natural and professional Korean**:\n\n"
        f"{final_summary}"
    )


    translate_prompt = ChatPromptTemplate.from_template(translate_template)
    translate_chain = translate_prompt | llm | StrOutputParser()


    translated = await translate_chain.ainvoke({"final_summary" : state["final_summary"]})
    logger.info(f"translated = {translated}")

    return {"translated_summary": translated}


graph_builder = StateGraph(OverallState)
graph_builder.add_node("generate_summary_node", generate_summary_node)
graph_builder.add_node("collect_summaries_node", collect_summaries_node)
graph_builder.add_node("collapse_summaries_node", collapse_summaries_node)
graph_builder.add_node("generate_final_summary_node", generate_final_summary_node)
graph_builder.add_node("translate_to_korean_node", translate_to_korean_node)

graph_builder.add_conditional_edges(START, map_summaries_edge, ["generate_summary_node"])
graph_builder.add_edge("generate_summary_node", "collect_summaries_node")
graph_builder.add_conditional_edges("collect_summaries_node", should_collapse_edge)
graph_builder.add_conditional_edges("collapse_summaries_node", should_collapse_edge)
graph_builder.add_edge("generate_final_summary_node", "translate_to_korean_node")
graph_builder.add_edge("translate_to_korean_node", END)

map_reduce_graph = graph_builder.compile()