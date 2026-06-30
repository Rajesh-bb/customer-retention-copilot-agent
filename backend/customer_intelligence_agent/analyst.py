from customer_intelligence_agent.healthscore import all_health_score
from datetime import date
from customer_intelligence_agent.healthscore import session
from tables import *
from datetime import timedelta
0-49
50-69
70-89
90-100

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
                self.high_risk_id.append(data["account_id"])

            elif data["total_score"]>=50 and data["total_score"]<=69 :
                self.medium_risk_id.append(data["account_id"])

            elif data["total_score"]>=70 and data["total_score"]<=89 :
                self.low_risk_id.append(data["account_id"])
            
            else:
                self.healthy_id.append(data["account_id"])
    def high_risk_analysis(self):
        result : list[dict] = []
        for data in self.high_risk_id:
            result_element = {}
            csm_note = session.query(CsmNotes.note).filter( CsmNotes.account_id == data , CsmNotes.created_at < self.date , CsmNotes.created_at >= self.date-timedelta(days = 30)).all()

            emails_result = session.query(Emails.body).filter(Emails.account_id == data,Emails.timestamp<self.date,Emails.timestamp>=self.date-timedelta(days=30)).all()

            ticket_messages_result = session.query(TicketMessage.message_body,Ticket.description).join(Ticket,Ticket.ticket_id ==TicketMessage.ticket_id).filter(Ticket.account_id == data,TicketMessage.timestamp<self.date,TicketMessage.timestamp>=self.date-timedelta(days = 30)).all()

            transcripts_result = session.query(CallTranscripts.transcript).filter(CallTranscripts.account_id==data,CallTranscripts.date<self.date,CallTranscripts.date>=self.date-timedelta(days = 30)).all()
            ticket_result = session.query(Ticket.description).filter(Ticket.account_id == data,Ticket.created_at<self.date,Ticket.created_at>=self.date-timedelta(days=30)).all()

            meetings_result = session.query(Meetings.notes).filter(Meetings.account_id == data,Meetings.date<self.date,Meetings.date>=self.date-timedelta(days=30)).all()

            billing_result = session.query(BillingEvents.event_description).filter(BillingEvents.account_id == data,BillingEvents.created_at<self.date,BillingEvents.created_at>=self.date-timedelta(days = 30)).all()
            result_element["account_id"] = data

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


            
           





    