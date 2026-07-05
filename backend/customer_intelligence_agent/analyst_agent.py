from langchain_google_genai import ChatGoogleGenerativeAI
import requests
from langgraph.graph import StateGraph, START, END
from langchain.tools import tool
from typing_extensions import TypedDict
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from typing import Annotated
from dotenv import load_dotenv
from backend.logger.custom_logger import logger
from langchain_core.messages import AIMessage
from concurrent.futures import ThreadPoolExecutor
import json
import os
load_dotenv()

key_1 = os.getenv("GOOGLE_API_KEY_1")
key_2 = os.getenv("GOOGLE_API_KEY_2")

class State(TypedDict):
    as_of_date: str
    accounts: list[dict]
    summaries: list[dict]
    messages: Annotated[list, add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash",api_key = key_2)


@tool
def get_high_risk_analysis(as_of_date: str):
    """Use this tool to get the reason for all the high-risk accounts for a specific date (YYYY-MM-DD)."""
    req = requests.get(f"http://localhost:8000/analyst?as_of_date={as_of_date}")
    logger.info("got the high risk account and their health scores")
    return req.json()

llm_with_tools = llm.bind_tools([get_high_risk_analysis])


def chatbot(state: State):
    output = llm_with_tools.invoke(state["messages"])
    return {"messages": [output]}

def summarize_reasons(state: State):
    """Get the summary of the reasons of all the accounts."""

    last_message = state["messages"][-1]
    accounts_data = last_message.content
    batch1 = accounts_data[:len(accounts_data)//2]
    batch2 = accounts_data[len(accounts_data)//2:]
    # print("the last account data : ")
    # print(accounts_data)
    llm_1 = ChatGoogleGenerativeAI(model="gemini-3.5-flash",api_key = key_2)
    llm_2 = ChatGoogleGenerativeAI(model="gemini-3.5-flash",api_key = key_2)
    logger.info("summarizer agent is initialized")

    prompt1 = f"""You are a Customer Success Analyst.

                You will receive a list of account dictionaries.

                Your task is:

                For EACH account:
                1. Read all available fields (emails, tickets, ticket_messages, meetings, call_transcripts, csm_notes, billing events, etc.).
                2. Identify the main customer issues.
                3. Merge duplicate information.
                4. Remove redundant details.
                5. Keep only the most important facts.
                6. Write a concise summary in 2–4 sentences.

                IMPORTANT OUTPUT REQUIREMENTS:

                - Return ONLY a valid JSON array.
                - The output MUST be valid JSON that can be parsed directly using Python's json.loads().
                - DO NOT include any explanation.
                - DO NOT include any introductory or concluding text.
                - DO NOT include markdown.
                - DO NOT wrap the output inside ```json or ``` code fences.
                - DO NOT include comments.
                - DO NOT include trailing commas.
                - DO NOT output anything except the JSON array.
                - Every object MUST contain exactly these two keys:
                    - "account_id"
                    - "reason"
                - Preserve the original account_id exactly as provided.
                - The "reason" must be a plain string.

                The required output format is:

                [
                {{
                    "account_id": "<account_id>",
                    "reason": "<concise summary>"
                }}
                ]

                Input:
                {batch1}"""
    prompt2 = f"""You are a Customer Success Analyst.

                You will receive a list of account dictionaries.

                Your task is:

                For EACH account:
                1. Read all available fields (emails, tickets, ticket_messages, meetings, call_transcripts, csm_notes, billing events, etc.).
                2. Identify the main customer issues.
                3. Merge duplicate information.
                4. Remove redundant details.
                5. Keep only the most important facts.
                6. Write a concise summary in 2–4 sentences.

                IMPORTANT OUTPUT REQUIREMENTS:

                - Return ONLY a valid JSON array.
                - The output MUST be valid JSON that can be parsed directly using Python's json.loads().
                - DO NOT include any explanation.
                - DO NOT include any introductory or concluding text.
                - DO NOT include markdown.
                - DO NOT wrap the output inside ```json or ``` code fences.
                - DO NOT include comments.
                - DO NOT include trailing commas.
                - DO NOT output anything except the JSON array.
                - Every object MUST contain exactly these two keys:
                    - "account_id"
                    - "reason"
                - Preserve the original account_id exactly as provided.
                - The "reason" must be a plain string.

                The required output format is:

                [
                {{
                    "account_id": "<account_id>",
                    "reason": "<concise summary>"
                }}
                ]

                Input:
                {batch2}"""
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(llm_1.invoke, prompt1)
        future2 = executor.submit(llm_2.invoke, prompt2)

        response1 = future1.result()
        response2 = future2.result()  # AIMessage

    list1 = json.loads(response1.content[0]["text"])
    list2 = json.loads(response2.content[0]["text"])

    combined = list1 + list2

    logger.info(" completed summarizing the reason for high risk accounts")
    # print(type(response))
    # print(type(response.content))
    # print(response.content)
    return {
    "messages": [
        AIMessage(content=json.dumps(combined))
    ]
}

builder = StateGraph(State)

tool_node = ToolNode([get_high_risk_analysis])

builder.add_node("llm", chatbot)
builder.add_node("get_high_risk_analysis", tool_node)
builder.add_node("summarizer", summarize_reasons)

builder.add_edge(START, "llm")

builder.add_conditional_edges("llm", tools_condition, {"tools": "get_high_risk_analysis", END: END})
builder.add_edge("get_high_risk_analysis", "summarizer")
builder.add_edge("summarizer", END)

app = builder.compile()


if __name__ == "__main__":
    print("Agent initialized. Type 'quit' to exit.")
    while True:
        user_input = input("\nUser: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break

        events = app.stream(
            {"messages": [("user", user_input)]},
            stream_mode="values"
        )

        # for event in events:
        #     if "messages" in event:
        #         last_msg = event["messages"][-1]

        #         print("Message type:", last_msg.type)
        #         print("Content type:", type(last_msg.content))
        #         print("Raw content:")
        #         print(repr(last_msg.content))
        for event in events:
            if "messages" in event:
                last_msg = event["messages"][-1]
                
                if last_msg.type == "ai" and last_msg.content:
                    
                    if isinstance(last_msg.content, list):
                        clean_text = "".join(block["text"] for block in last_msg.content if "text" in block)
                        print(f"Bot: {clean_text}")
                    
                    else:
                        print(f"Bot: {last_msg.content}")