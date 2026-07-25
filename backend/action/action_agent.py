from typing_extensions import TypedDict
from backend.recommendation.recommendation import recommendation_graph
from backend.customer_intelligence_agent.healthscore import session
from backend.data_ingestion.tables import Contact
from backend.action.actions import payload_emails, send_email,schedule_meeting
from langgraph.types import interrupt,Command
from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime
import os
from backend.recommendation.recommendation import State
from backend.action.report_generator import generate_report as report_generator
from backend.RAG.vector_store import build_vector_store
from backend.logger.custom_logger import logger

from dotenv import load_dotenv
load_dotenv()

class State(TypedDict):
    recommendations: list[dict]
    payload: list[dict]
    # full_recommendations : list[dict]
    user_input: str
    current_index: int
    approval: list[dict]
    execution_result: list[dict]
    analyst_output: list[dict]
    analysis_date : datetime
    report: dict
    messages: list
    execute_actions: bool

llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY_1")
) 

def execute_action_agent(
    query: str,
    execute_actions: bool = True
):

    config = {
        "configurable": {
            "thread_id": "slack-test"
        }
    }

    result = graph.invoke(
        {
            "user_input": query,
            "execute_actions": execute_actions
        },
        config=config
    )

    if not execute_actions:
        return result

    while "__interrupt__" in result:

        print(result["__interrupt__"])

        payload = result["__interrupt__"][0].value

        while True:

            decision = input("Approve/Reject/Edit: ").lower()

            if decision in ["approve", "reject", "edit"]:
                break

            print("Invalid input!")

        if decision == "edit":

            while True:

                print(f"""
1. Action              : {payload["action"]}
2. Reason              : {payload["reason"]}
""")

                if "email" in payload:
                    print(f"3. Email Subject       : {payload['email']['subject']}")
                    print(f"4. Email Body          : {payload['email']['body']}")

                if "meeting" in payload:
                    print(f"5. Meeting Subject     : {payload['meeting']['subject']}")
                    print(f"6. Meeting Description : {payload['meeting']['description']}")

                print("0. Finish Editing")

                choice = input("Enter field number: ")

                if choice == "0":
                    break

                elif choice == "1":
                    payload["action"] = input("New action: ")

                elif choice == "2":
                    payload["reason"] = input("New reason: ")

                elif choice == "3" and "email" in payload:
                    payload["email"]["subject"] = input("New email subject: ")

                elif choice == "4" and "email" in payload:
                    payload["email"]["body"] = input("New email body: ")

                elif choice == "5" and "meeting" in payload:
                    payload["meeting"]["subject"] = input("New meeting subject: ")

                elif choice == "6" and "meeting" in payload:
                    payload["meeting"]["description"] = input("New meeting description: ")

                else:
                    print("Invalid choice!")

            approval = {
                "decision": "approve",
                "payload": payload
            }

        else:

            approval = {
                "decision": decision,
                "payload": payload
            }

        result = graph.invoke(
            Command(resume=approval),
            config=config
        )

    return result

def extract_date(user_input: str):

    prompt = f"""
    Extract the analysis date from the following query.

    Rules:
    - Return ONLY one value.
    - Either a date in YYYY-MM-DD format.
    - Or null.
    - No explanation.
    - No markdown.
    - No quotes.

    Query:
    {user_input}
    """

    response = llm.invoke(prompt)

    output = response.text.strip()

    if output.lower() == "null":
        return None

    return datetime.strptime(output, "%Y-%m-%d").date()

def start_node(state: State):
    return {
        "current_index": 0,
        "approval": [],
        "execution_result": [],
        "analysis_date": extract_date(state["user_input"])
    }


def prepare_payload(state: State):

    result = recommendation_graph.invoke({
        "user_input": state["user_input"]
    })
    logger.info("built vector store")
    build_vector_store(
    result["structured_input"],state["analysis_date"]
    )
    recommendations = result["recommendations"]

    # full_recommendations = recommendations.copy()

    payload = []

    for rec in recommendations:

        element = {}

        account_id = rec["account_id"]

        element["account_id"] = account_id
        element["action"] = rec["recommended_action"]
        element["requires_human_approval"] = rec["requires_human_approval"]
        element["reason"] = rec["reason"]
        element["status_approval"] = "pending_approval"

        account = (
            session.query(Contact)
            .filter(
                Contact.account_id == account_id,
                Contact.decision_maker_flag == True
            )
            .first()
        )

        if account is not None:

            meta_data = {
                "name": account.name,
                "job_title": account.job_title,
                "email": account.email
            }

            element["meta_data"] = meta_data
            payload.append(element)
            payload = payload[:5]   # only for the testing

    return {"payload": payload,"analyst_output": result["analyst_output"]}


def prepare_action_details(state: State):

    for element in state["payload"]:
        # print(element["action"])
        # print(payload_emails.keys())

        if element["action"] == "schedule_meeting":

            element["meeting"] = {
                "subject": "Customer Success Check-in",
                "customer_email": element["meta_data"]["email"],
                "description": element["reason"]
            }

        elif element["action"] == "monitor_only":
            continue

        else:

            template = payload_emails.get(element["action"])

            if template is None:
                continue

            element["email"] = {
                "to": element["meta_data"]["email"],
                "subject": template["subject"],
                "body": template["body"].format(
                    name=element["meta_data"]["name"]
                )
            }

    return {"payload": state["payload"]}

def route_after_prepare(state: State):

    if state["execute_actions"]:
        return "human_approval"

    return "generate_report"

def human_approval(state: State):

    current_payload = state["payload"][state["current_index"]]

    response = interrupt(current_payload)
    #print(response) # only for debugging

    return {
        "approval": state["approval"] + [response],
        "current_index": state["current_index"] + 1
    }


def should_continue(state: State):

    if state["current_index"] < len(state["payload"]):
        return "human_approval"

    return "execute_action"


def execute_action(state: State):

    execution_result = []
    count = 0 # only for the testing purpose
    analysis_date = extract_date(state["user_input"])
    next_hr = 9
    for approval in state["approval"]:

        if approval["decision"] == "reject":
            continue
        payload = approval["payload"]

        if payload["action"] == "schedule_meeting":

            try:
                meeting_result = schedule_meeting(
                    customer_email=payload["meeting"]["customer_email"],
                    subject=payload["meeting"]["subject"],
                    description=payload["meeting"]["description"],
                    as_of_date=analysis_date,
                    start_hr = next_hr
                )
                next_hr = next_hr + 1

            except Exception as e:

                meeting_result = {
                    "status": "failed",
                    "error": str(e)
                }

            execution_result.append({
                "account_id": payload["account_id"],
                "action": "schedule_meeting",
                "result": meeting_result
            })

        elif payload["action"] == "monitor_only":
            continue

        else:

            if count <=5: # only for the testing  

                if "email" not in payload:
                    print(f"Email not present for action: {payload['action']}")
                    continue

                try:
                    print(payload["email"]["subject"])
                    email_result = send_email(
                        to="s.rajesh17092004@gmail.com",      
                        subject=payload["email"]["subject"],
                        body=payload["email"]["body"]
                    )

                except Exception as e:

                    print(e)

                    email_result = {
                        "status": "failed",
                        "error": str(e)
                    }

                execution_result.append({
                    "account_id": payload["account_id"],
                    "action": "send_email",
                    "result": email_result
                })

                count += 1 

    return {
        "execution_result": execution_result
    }

def generate_report(state: State):

    report = report_generator(
        state["analyst_output"],analysis_date = state["analysis_date"]
    )

    return {
        "report": report
    }



builder = StateGraph(State)

builder.add_node("start",start_node)
builder.add_node("prepare_payload",prepare_payload)
builder.add_node("prepare_action_details",prepare_action_details)
builder.add_node("human_approval",human_approval)
# builder.add_node("should_continue",should_continue)
builder.add_node("execute_action",execute_action)

builder.add_node("generate_report", generate_report)

builder.add_edge(START, "start")
builder.add_edge("start", "prepare_payload")
builder.add_edge("prepare_payload", "prepare_action_details")
# builder.add_edge("prepare_action_details", "human_approval")
builder.add_conditional_edges(
    "prepare_action_details",
    route_after_prepare,
    {
        "human_approval": "human_approval",
        "generate_report": "generate_report",
    },
)
builder.add_conditional_edges(
    "human_approval",
    should_continue,
    {
        "human_approval": "human_approval",
        "execute_action": "execute_action",
    },
)

builder.add_edge("execute_action", "generate_report")
builder.add_edge("generate_report", END)

# builder.add_edge("execute_action", END)

graph = builder.compile(checkpointer=InMemorySaver())

if __name__ == "__main__":

    # graph = builder.compile(checkpointer=InMemorySaver())

    config = {"configurable": {"thread_id": "test-1"}}

    user_input = input("Enter your query: ")

    result = graph.invoke(
        {"user_input": user_input, "execute_actions": True},
        config=config
    )

   
    while "__interrupt__" in result:

        print(result["__interrupt__"])

        payload = result["__interrupt__"][0].value

        while True:
            decision = input("Approve/Reject/Edit: ").lower()

            if decision in ["approve", "reject", "edit"]:
                break

            print("Invalid input!")

        if decision == "edit":

            while True:

                print(f"""
                1. Action              : {payload["action"]}
                2. Reason              : {payload["reason"]}
                """)

                if "email" in payload:
                    print(f"3. Email Subject       : {payload['email']['subject']}")
                    print(f"4. Email Body          : {payload['email']['body']}")

                if "meeting" in payload:
                    print(f"5. Meeting Subject     : {payload['meeting']['subject']}")
                    print(f"6. Meeting Description : {payload['meeting']['description']}")

                print("0. Finish Editing")

                choice = input("Enter field number: ")

                if choice == "0":
                    break

                elif choice == "1":
                    payload["action"] = input("New action: ")

                elif choice == "2":
                    payload["reason"] = input("New reason: ")

                elif choice == "3" and "email" in payload:
                    payload["email"]["subject"] = input("New email subject: ")

                elif choice == "4" and "email" in payload:
                    payload["email"]["body"] = input("New email body: ")

                elif choice == "5" and "meeting" in payload:
                    payload["meeting"]["subject"] = input("New meeting subject: ")

                elif choice == "6" and "meeting" in payload:
                    payload["meeting"]["description"] = input("New meeting description: ")
                print(payload["email"]["subject"]) 
            approval = {
                    "decision": "approve",
                    "payload": payload
                }

        else:

            approval = {
                        "decision": decision,
                        "payload": payload
                    }

        result = graph.invoke(
            Command(resume=approval),
            config=config
        )
        
    print(result)

