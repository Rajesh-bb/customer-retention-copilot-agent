from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from .customer_intelligence_agent.healthscore import *
from .data_ingestion.tables import * 
from .customer_intelligence_agent.analyst import Analyst
from backend.RAG.chatbot import chatbot
from pydantic import BaseModel
from backend.CSM.csm_agent import csm_agent
from backend.action.action_agent import resume_action_agent
from typing import Any, Optional
from uuid import uuid4


class ChatRequest(BaseModel):
    thread_id: Optional[str] = None
    message: str

class ApprovalRequest(BaseModel):
    thread_id: str
    approval: dict

class ChatResponse(BaseModel):
    type: str
    thread_id: str
    response: Optional[Any] = None
    payload: Optional[dict] = None
    graph_state: Optional[dict] = None
    operation: Optional[str] = None

    
app = FastAPI()

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    try:
        thread_id = request.thread_id

        if not thread_id:
            thread_id = str(uuid4())

        result = csm_agent(
            user_input=request.message,
            thread_id=thread_id,
            execute_action=True,
        )
        print("FastAPI received:")
        print(result)

        if result.get("status") == "waiting_for_approval":
            print(result)
            import pprint

            print("===================")
            pprint.pprint(result["payload"])
            print(type(result["payload"]))
            print("===================")
            return ChatResponse(
                type="approval",
                thread_id = thread_id,
                payload = result["payload"],
                operation=None,
            )

        if result.get("analysis_ran"):
            response = result["response"].content # 

            if isinstance(response, list):
                response = "".join(
                    block["text"]
                    for block in response
                    if block.get("type") == "text"
                )
            return ChatResponse(
                type="report",
                thread_id=thread_id,
                response=response,
                graph_state=result["graph_state"],
                operation=result["operation"],
            )
        
        response = result["response"].content #

        if isinstance(response, list):
            response = "".join(
                block["text"]
                for block in response
                if block.get("type") == "text"
            )

        return ChatResponse(
            type="chat",
            thread_id=thread_id,
            response=response,
            operation=result["operation"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error while processing chat request: {str(e)}"
        )


@app.post("/approval", response_model=ChatResponse)
def approval(request: ApprovalRequest):

    try:
        result = resume_action_agent(
            approval=request.approval,
            thread_id=request.thread_id,
        )

        if result.get("status") == "waiting_for_approval":
            return ChatResponse(
                type="approval",
                thread_id=request.thread_id,
                payload=result["payload"],
            )

        return ChatResponse(
            type="report",
            thread_id=request.thread_id,
            graph_state=result["result"]["report"],
            operation="analysis",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error while processing approval request: {str(e)}"
        )

# @app.post("/chat")
# def chat(request: ChatRequest):

#     thread_id = request.thread_id

#     if not thread_id:
#         thread_id = str(uuid4())

#     result = csm_agent(
#         user_input=request.message,
#         thread_id=thread_id,
#         execute_action=True,
#     )

#     if result.get("status") == "waiting_for_approval":
#         return {
#             "type": "approval",
#             "thread_id": thread_id,
#             "payload": result["payload"],
#         }

#     if result.get("analysis_ran"):
#         return {
#             "type": "report",
#             "thread_id": thread_id,
#             "response": result["response"].content,
#             "graph_state": result["graph_state"],
#         }

#     return {
#         "type": "chat",
#         "thread_id": thread_id,
#         "response": result["response"].content,
#     }


# @app.post("/approval")
# def approval(request: ApprovalRequest):

#     result = resume_action_agent(
#         approval=request.approval,
#         thread_id=request.thread_id,
#     )

#     if result.get("status") == "waiting_for_approval":
#         return {
#             "type": "approval",
#             "thread_id": request.thread_id,
#             "payload": result["payload"],
#         }

#     return {
#         "type": "report",
#         "thread_id": request.thread_id,
#         "graph_state": result["result"],
#     }



# class ReturnHealthScore(BaseModel):
#     account_id : str
#     current_5d_events : int
#     previous_5d_events : int
#     older_5d_events : int
#     usage_status : str
#     usage_score : int
#     ticket_score : int
#     volume_score :int
#     resolution_score : int
#     severity_score : int
#     total_score : int

# @app.get("/health_score/{account_id}", response_model=ReturnHealthScore)
# def get_health_score(account_id : str, as_of_date : date):

#     result = health_score(account_id,as_of_date)

#     return ReturnHealthScore(**result)
# @app.get("/all_health_score")
# def get_all_health_score(as_of_date : date):

#     all_result = all_health_score(as_of_date=as_of_date)

#     return all_result

# @app.get("/analyst_all")
# def get_all_risk_analysis(as_of_date : date):
#     all_result = all_health_score(as_of_date = as_of_date)
#     analyst = Analyst(all_result=all_result,as_of_data=as_of_date)
#     result = analyst.high_risk_analysis()
#     random.shuffle(result)
#     return result

# @app.get("/analyst_high")
# def get_high_risk_analysis(as_of_date : date):
#     all_result = all_health_score(as_of_date = as_of_date)
#     analyst = Analyst(all_result=all_result,as_of_data=as_of_date)
#     high = analyst.high_risk_analysis()
#     medium = analyst.medium_risk_analysis()
#     low = analyst.low_risk_analysis()
#     healthy = analyst.healthy_risk_analysis()
#     result = high + medium + low + healthy
#     return result

# @app.get("/analyst_medium")
# def get_low_risk_analysis(as_of_date : date):
#     all_result = all_health_score(as_of_date = as_of_date)
#     analyst = Analyst(all_result=all_result,as_of_data=as_of_date)
#     result = analyst.medium_risk_analysis()
#     return result

# @app.get("/analyst_low")
# def get_medium_risk_analysis(as_of_date : date):
#     all_result = all_health_score(as_of_date = as_of_date)
#     analyst = Analyst(all_result=all_result,as_of_data=as_of_date)
#     result = analyst.low_risk_analysis()
#     return result

# @app.get("/analyst_healthy")
# def get_healthy_risk_analysis(as_of_date : date):
#     all_result = all_health_score(as_of_date = as_of_date)
#     analyst = Analyst(all_result=all_result,as_of_data=as_of_date)
#     result = analyst.healthy_risk_analysis()
#     return result

# class ChatRequest(BaseModel):
#     question: str
# @app.post("/chat")
# def chat(request: ChatRequest):

#     answer = chatbot(request.question)

#     return {
#         "answer": answer
#     }

# class CSMRequest(BaseModel):
#     user_input: str


# @app.post("/csm/chat")
# def csm_chat(request: CSMRequest,execute_action = False):
#     result = csm_agent(
#         request.user_input,execute_action=False
#     )
#     return {
#             "response": result["response"].content[0]["text"],
#             "report_pdf": "reports/customer_retention_report.pdf"
#         }








