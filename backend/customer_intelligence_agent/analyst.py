from backend.customer_intelligence_agent.healthscore import all_health_score
from datetime import date
from backend.customer_intelligence_agent.healthscore import session
from backend.data_ingestion.tables import *
from datetime import timedelta
0-49
50-69
70-89
90-100

def get_info(input_list,input_date):
    result : list[dict] = []
    for data in input_list:
        result_element = {}
        account_id = data["account_id"]
        csm_note = session.query(CsmNotes.note).filter( CsmNotes.account_id == account_id , CsmNotes.created_at < input_date , CsmNotes.created_at >= input_date-timedelta(days = 30)).all()

        emails_result = session.query(Emails.body).filter(Emails.account_id == account_id,Emails.timestamp<input_date,Emails.timestamp>=input_date-timedelta(days=30)).all()

        ticket_messages_result = session.query(TicketMessage.message_body,Ticket.description).join(Ticket,Ticket.ticket_id ==TicketMessage.ticket_id).filter(Ticket.account_id == account_id,TicketMessage.timestamp<input_date,TicketMessage.timestamp>=input_date-timedelta(days = 30)).all()

        transcripts_result = session.query(CallTranscripts.transcript).filter(CallTranscripts.account_id==account_id,CallTranscripts.date<input_date,CallTranscripts.date>=input_date-timedelta(days = 30)).all()
        ticket_result = session.query(Ticket.description).filter(Ticket.account_id == account_id,Ticket.created_at<input_date,Ticket.created_at>=input_date-timedelta(days=30)).all()

        meetings_result = session.query(Meetings.notes).filter(Meetings.account_id == account_id,Meetings.date<input_date,Meetings.date>=input_date-timedelta(days=30)).all()

        billing_result = session.query(BillingEvents.event_description).filter(BillingEvents.account_id == account_id,BillingEvents.created_at<input_date,BillingEvents.created_at>=input_date-timedelta(days = 30)).all()
        result_element["account_id"] = account_id
        result_element["risk_level"] = data["risk_level"]


        csm_note = [row.note for row in csm_note]
        emails_result = [row.body for row in emails_result]
        ticket_messages_result = [row.message_body for row in ticket_messages_result]
        ticket_result = [row.description for row in ticket_result]
        transcripts_result = [row.transcript for row in transcripts_result]
        meetings_result = [row.notes for row in meetings_result]
        billing_result = [row.event_description for row in billing_result]
        if csm_note :
            result_element["csm"] = csm_note
        if emails_result :
            result_element["emails"] = emails_result
        if ticket_messages_result :
            result_element["ticket_messages"] = ticket_messages_result
        if ticket_result :
            result_element["tickets"] = ticket_result
        if transcripts_result :
            result_element["call_transcripts"] = transcripts_result
        if meetings_result :
            result_element["meetings"] = meetings_result
        if billing_result :
            result_element["billings"] = billing_result

        result.append(result_element)
    return result


class Analyst:
    def __init__(self, all_result : list[dict],as_of_data : date):
        self.input = all_result
        self.date = as_of_data
        # now separate the ids according to the risk
        self.high_risk_id = []
        self.medium_risk_id = []
        self.low_risk_id = []
        self.healthy_id = []
        for data in all_result:
            if data["total_score"]<=49:
                self.high_risk_id.append({"account_id" : data["account_id"], "risk_level" : "high"})

            elif data["total_score"]>=50 and data["total_score"]<=69 :
                self.medium_risk_id.append({"account_id" : data["account_id"], "risk_level" : "medium"})

            elif data["total_score"]>=70 and data["total_score"]<=89 :
                self.low_risk_id.append({"account_id" : data["account_id"], "risk_level" : "low"})
            
            else:
                self.healthy_id.append({"account_id" : data["account_id"], "risk_level" : "healthy"})
    def high_risk_analysis(self):
        return get_info(self.high_risk_id,self.date)
    def medium_risk_analysis(self):
        return get_info(self.medium_risk_id,self.date)
    def low_risk_analysis(self):
        return get_info(self.low_risk_id,self.date)
    def healthy_risk_analysis(self):
        return get_info(self.healthy_id,self.date)
        

            
           





    