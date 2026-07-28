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
from backend.customer_intelligence_agent.healthscore import all_health_score
from backend.customer_intelligence_agent.analyst import Analyst
from datetime import date
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

llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite",api_key = key_2)

@tool
def get_all_risk_analysis(as_of_date: str):
    """Use this tool to get the reason for all the accounts for a specific date (YYYY-MM-DD)."""
    as_of_date = date.fromisoformat(as_of_date)
    all_result = all_health_score(as_of_date=as_of_date)

    analyst = Analyst(
        all_result=all_result,
        as_of_data=as_of_date,
    )

    high = analyst.high_risk_analysis()
    medium = analyst.medium_risk_analysis()
    low = analyst.low_risk_analysis()
    healthy = analyst.healthy_risk_analysis()

    result = high + medium + low + healthy

    logger.info("got the account analysis")

    return result


@tool
def get_high_risk_analysis(as_of_date: str):
    """Use this tool to get the reason for all the high-risk accounts for a specific date (YYYY-MM-DD)."""
    as_of_date = date.fromisoformat(as_of_date)
    all_result = all_health_score(as_of_date=as_of_date)

    analyst = Analyst(
        all_result=all_result,
        as_of_data=as_of_date,
    )

    result = analyst.high_risk_analysis()

    logger.info("got the healthy accounts")

    return result
@tool
def get_medium_risk_analysis(as_of_date: str):
    """Use this tool to get the reason for all the medium-risk accounts for a specific date (YYYY-MM-DD)."""
    as_of_date = date.fromisoformat(as_of_date)
    all_result = all_health_score(as_of_date=as_of_date)

    analyst = Analyst(
        all_result=all_result,
        as_of_data=as_of_date,
    )

    result = analyst.medium_risk_analysis()

    logger.info("got the medium risk accounts")

    return result

@tool
def get_low_risk_analysis(as_of_date: str):
    """Use this tool to get the reason for all the low-risk accounts for a specific date (YYYY-MM-DD)."""
    as_of_date = date.fromisoformat(as_of_date)
    all_result = all_health_score(as_of_date=as_of_date)

    analyst = Analyst(
        all_result=all_result,
        as_of_data=as_of_date,
    )

    result = analyst.low_risk_analysis()

    logger.info("got the low risk accounts")

    return result

@tool
def get_healthy_analysis(as_of_date: str):
    """Use this tool to get the reason for all the healthy accounts for a specific date (YYYY-MM-DD)."""
    as_of_date = date.fromisoformat(as_of_date)
    all_result = all_health_score(as_of_date=as_of_date)

    analyst = Analyst(
        all_result=all_result,
        as_of_data=as_of_date,
    )

    result = analyst.healthy_risk_analysis()
    logger.info("got the healthy accounts")
    return result

llm_with_tools = llm.bind_tools([get_high_risk_analysis,get_medium_risk_analysis,get_low_risk_analysis,get_healthy_analysis,get_all_risk_analysis])


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
    llm_1 = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite",api_key = key_2)
    llm_2 = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite",api_key = key_2)
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
                Each account dictionary also contains a "risk_level" field.

                The risk_level is an important business context and MUST be considered while summarizing.

                If risk_level is "HIGH":
                - Summarize the primary reasons that make the account high risk.
                - Focus on churn signals, customer dissatisfaction, unresolved issues, billing problems, adoption issues, support issues, and business risks.
                - Do NOT describe the account as healthy, stable, or an expansion opportunity.
                - The summary should explain why the account is high risk based on the available evidence.

                If risk_level is "MEDIUM":
                - Summarize the primary reasons that make the account medium risk.
                - Focus on moderate churn signals, declining adoption, unresolved customer concerns, onboarding challenges, billing concerns, or reduced engagement.
                - Highlight both positive and negative signals if they coexist.
                - The summary should explain why the account requires proactive attention to prevent becoming high risk.

                If risk_level is "LOW":
                - Summarize the primary reasons that make the account low risk.
                - Focus on generally healthy customer behavior while mentioning any minor issues, feature requests, or adoption opportunities.
                - Emphasize overall customer satisfaction and stable product usage.
                - The summary should explain why the account remains healthy with only minor risks or opportunities for improvement.

                If risk_level is "HEALTHY":
                - Summarize the primary reasons that make the account healthy.
                - Focus on strong adoption, positive customer feedback, successful outcomes, expansion opportunities, and high engagement.
                - Mention only significant positive signals unless a minor issue requires attention.
                - The summary should explain why the account is healthy and highlight opportunities to strengthen the customer relationship further.

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
                Each account dictionary also contains a "risk_level" field.

                The risk_level is an important business context and MUST be considered while summarizing.

                If risk_level is "HIGH":
                - Summarize the primary reasons that make the account high risk.
                - Focus on churn signals, customer dissatisfaction, unresolved issues, billing problems, adoption issues, support issues, and business risks.
                - Do NOT describe the account as healthy, stable, or an expansion opportunity.
                - The summary should explain why the account is high risk based on the available evidence.

                If risk_level is "MEDIUM":
                - Summarize the primary reasons that make the account medium risk.
                - Focus on moderate churn signals, declining adoption, unresolved customer concerns, onboarding challenges, billing concerns, or reduced engagement.
                - Highlight both positive and negative signals if they coexist.
                - The summary should explain why the account requires proactive attention to prevent becoming high risk.

                If risk_level is "LOW":
                - Summarize the primary reasons that make the account low risk.
                - Focus on generally healthy customer behavior while mentioning any minor issues, feature requests, or adoption opportunities.
                - Emphasize overall customer satisfaction and stable product usage.
                - The summary should explain why the account remains healthy with only minor risks or opportunities for improvement.

                If risk_level is "HEALTHY":
                - Summarize the primary reasons that make the account healthy.
                - Focus on strong adoption, positive customer feedback, successful outcomes, expansion opportunities, and high engagement.
                - Mention only significant positive signals unless a minor issue requires attention.
                - The summary should explain why the account is healthy and highlight opportunities to strengthen the customer relationship further.
                

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

    logger.info(" completed summarizing the reason for accounts")
    # print(type(response))
    # print(type(response.content))
    # print(response.content)
    return {
    "messages": [
        AIMessage(content=json.dumps(combined))
    ]
}

builder = StateGraph(State)

tool_node = ToolNode([
    get_high_risk_analysis,
    get_medium_risk_analysis,
    get_low_risk_analysis,
    get_healthy_analysis,
    get_all_risk_analysis
])

builder.add_node("llm", chatbot)
builder.add_node("tools", tool_node)
builder.add_node("summarizer", summarize_reasons)

builder.add_edge(START, "llm")

builder.add_conditional_edges("llm", tools_condition, {"tools": "tools", END: END})
builder.add_edge("tools", "summarizer")
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