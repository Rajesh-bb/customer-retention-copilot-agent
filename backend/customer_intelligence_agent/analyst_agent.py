from langchain_google_genai import ChatGoogleGenerativeAI
import requests
from langgraph.graph import StateGraph, START, END
from langchain.tools import tool
from typing_extensions import TypedDict
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from typing import Annotated
from dotenv import load_dotenv

load_dotenv()

class State(TypedDict):
    as_of_date: str
    accounts: list[dict]
    summaries: list[dict]
    messages: Annotated[list, add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash")


@tool
def get_high_risk_analysis(as_of_date: str):
    """Use this tool to get the reason for all the high-risk accounts for a specific date (YYYY-MM-DD)."""
    req = requests.get(f"http://localhost:8000/analyst?as_of_date={as_of_date}")
    return req.json()

llm_with_tools = llm.bind_tools([get_high_risk_analysis])

def chatbot(state: State):
    output = llm_with_tools.invoke(state["messages"])
    return {"messages": [output]}

def summarize_reasons(state: State):
    """Get the summary of the reasons of all the accounts."""

    last_message = state["messages"][-1]
    accounts_data = last_message.content

    prompt = f"""You are a Customer Success analyst.
            You will receive a list of account dictionaries.
            For EACH account:
            1. Read all available fields (emails, tickets, ticket_messages, meetings, call_transcripts, csm_notes, etc.).
            2. Identify the main customer issues.
            3. Merge duplicate information.
            4. Keep only the most important facts.
            5. Write a concise summary (2-4 sentences).
            Return ONLY a JSON array.
            Output format:
            [
            {{
                "account_id": "<account_id>",
                "reason": "<concise summary>"
            }}
            ]
            Input:
            {accounts_data}"""
            
    response = llm.invoke(prompt)
    return {"messages": [response]}

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

        for event in events:
            if "messages" in event:
                last_msg = event["messages"][-1]
                
                if last_msg.type == "ai" and last_msg.content:
                    
                    if isinstance(last_msg.content, list):
                        clean_text = "".join(block["text"] for block in last_msg.content if "text" in block)
                        print(f"Bot: {clean_text}")
                    
                    else:
                        print(f"Bot: {last_msg.content}")