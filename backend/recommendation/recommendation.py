from backend.customer_intelligence_agent.analyst_agent import app as customer_agent
from langgraph.graph import StateGraph, START, END
from backend.data_ingestion.tables import Account
from backend.customer_intelligence_agent.healthscore import session
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Annotated
from langgraph.graph.message import add_messages
from backend.logger.custom_logger import logger
from langchain_core.messages import AIMessage
from concurrent.futures import ThreadPoolExecutor
from backend.prompts.recommendation_prompt import recommendation_prompt
import json
import os

key_1 = os.getenv("GOOGLE_API_KEY_1")
key_2 = os.getenv("GOOGLE_API_KEY_2")

class State(TypedDict):
    user_input: str
    structured_input: list[dict]
    recommendations: list[dict]
    messages: Annotated[list, add_messages]


def prepare_input(state: State):
    final_state = customer_agent.invoke(
        {"messages": [("user", state["user_input"])]}
    )
    last_message = final_state["messages"][-1].content

    try:
        last_message = json.loads(last_message)
    except json.JSONDecodeError:
        logger.error("invalid response from the summarizer node from the customer intelligence agent")
        raise
    #last_message = json.loads(last_message[0]["text"])
    structured_input = []
    #print(type(last_message))
    #print(last_message)

    for element in last_message:
        account_id = element["account_id"]

        account = (
            session.query(Account)
            .filter(Account.account_id == account_id)
            .one_or_none()
        )

        if account is None:
            continue

        account_data = {
            "account_id": account_id,
            "summary": element["reason"],
            # "health_score": element["health_score"],  
            "meta_data": {
                "renewal_date": account.renewal_date,
                "plan": account.plan,
                "archetype": account.archetype,
                "contract_value": account.contract_value,
                "industry": account.industry,
                "company_size": account.company_size,
            },
        }

        structured_input.append(account_data)

    return {"structured_input": structured_input}

agent = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",api_key = key_1)

def recommendation_agent(state : State):
    
    mid = len(state["structured_input"]) // 2
    batch1 = state["structured_input"][:mid]
    batch2 = state["structured_input"][mid:]
    agent1 = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",api_key = key_1)
    agent2 = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",api_key = key_1)
    logger.info("recommendation agent initialized")

    prompt1 = recommendation_prompt.invoke({"input" : batch1})
   
    prompt2 = recommendation_prompt.invoke({"input" : batch2})
   
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(agent1.invoke, prompt1)
        future2 = executor.submit(agent2.invoke, prompt2)

        output1 = future1.result()
        output2 = future2.result()
    try:
        list1 = json.loads(output1.content[0]["text"])
    except json.JSONDecodeError:
        logger.error("Invalid JSON from agent1: %s", output1.content)
        raise

    try:
        list2 = json.loads(output2.content[0]["text"])
    except json.JSONDecodeError:
        logger.error("Invalid JSON from agent2: %s", output2.content)
        raise
    recommendations = list1 + list2
    logger.info("recommendations prepared")
    return {
    "recommendations": recommendations,
    "messages": [AIMessage(content=json.dumps(recommendations))]
}

ALLOWED_ACTIONS = {
    "schedule_meeting",
    "send_training_material",
    "executive_escalation",
    "billing_review",
    "renewal_outreach",
    "upsell_proposal",
    "monitor_only",
}

ALLOWED_PRIORITIES = {"LOW", "MEDIUM", "HIGH"}

def validate(state : State):
    recommendations = state["recommendations"]
    logger.info("validation of recommendations")
    for rec in recommendations:
        if (
            rec["recommended_action"] not in ALLOWED_ACTIONS or
            rec["priority"] not in ALLOWED_PRIORITIES or
            not isinstance(rec["requires_human_approval"], bool)
        ):

            prompt = f"""
            The following JSON is invalid:

            {rec}

            Rules:
            - recommended_action must be one of {ALLOWED_ACTIONS}
            - priority must be one of {ALLOWED_PRIORITIES}
            - requires_human_approval must be true or false

            Return ONLY the corrected JSON.
            """

            corrected = agent.invoke(prompt)
            rec = json.loads(corrected.content)

    return {"recommendations": recommendations}

builder = StateGraph(State)
builder.add_node("input",prepare_input)
builder.add_node("agent",recommendation_agent)
builder.add_node("validate",validate)

builder.add_edge(START,"input")
builder.add_edge("input","agent")
builder.add_edge("agent","validate")
builder.add_edge("validate",END)

recommendation_graph = builder.compile()

if __name__== "__main__":
    print("agent initialized. type quit to exit")

    while True:
        u_input = input("\nUser: ")
        if u_input.lower() == "quit" :
            break

        #output = recommendation_graph.invoke({"user_input" : u_input})
        #print(output["recommendations"])
        output = recommendation_graph.invoke({"user_input": u_input})

        last_msg = output["messages"][-1]

        if isinstance(last_msg.content, list):
            clean_text = "".join(
                block["text"] for block in last_msg.content
                if block.get("type") == "text"
            )
            print(f"Bot: {clean_text}")
        else:
            print(f"Bot: {last_msg.content}")
    

