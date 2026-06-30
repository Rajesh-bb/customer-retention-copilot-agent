from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from customer_intelligence_agent.healthscore import *
from tables import * 
from customer_intelligence_agent.analyst import Analyst

app = FastAPI()

class ReturnHealthScore(BaseModel):
    account_id : str
    current_5d_events : int
    previous_5d_events : int
    older_5d_events : int
    usage_status : str
    usage_score : int
    ticket_score : int
    volume_score :int
    resolution_score : int
    severity_score : int
    total_score : int

@app.get("/health_score/{account_id}", response_model=ReturnHealthScore)
def get_health_score(account_id : str, as_of_date : date):

    result = health_score(account_id,as_of_date)

    return ReturnHealthScore(**result)


@app.get("/all_health_score")
def get_all_health_score(as_of_date : date):

    all_result = all_health_score(as_of_date=as_of_date)

    return all_result

@app.get("/analyst")
def get_analysis(as_of_date : date):
    all_result = all_health_score(as_of_date = as_of_date)
    analyst = Analyst(all_result=all_result,as_of_data=as_of_date)
    result = analyst.high_risk_analysis()
    return result














