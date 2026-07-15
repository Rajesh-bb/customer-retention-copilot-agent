from datetime import date, timedelta

from backend.customer_intelligence_agent.healthscore import session
from backend.data_ingestion.tables import (
    CsmNotes,
    Emails,
    Ticket,
    TicketMessage,
    CallTranscripts,
    Meetings,
    BillingEvents,
)

account_id = "ACC-6aa595031e51"
as_of_date = date(2025, 6, 1)
start_date = as_of_date - timedelta(days=30)

print(f"\nAccount: {account_id}")
print(f"Date Range: {start_date} -> {as_of_date}")

print("\n========== CSM NOTES ==========")
for row in session.query(CsmNotes.note).filter(
    CsmNotes.account_id == account_id,
    CsmNotes.created_at >= start_date,
    CsmNotes.created_at < as_of_date,
).all():
    print("-", row.note)

print("\n========== EMAILS ==========")
for row in session.query(Emails.body).filter(
    Emails.account_id == account_id,
    Emails.timestamp >= start_date,
    Emails.timestamp < as_of_date,
).all():
    print("-", row.body)

print("\n========== TICKETS ==========")
for row in session.query(Ticket.description).filter(
    Ticket.account_id == account_id,
    Ticket.created_at >= start_date,
    Ticket.created_at < as_of_date,
).all():
    print("-", row.description)

print("\n========== TICKET MESSAGES ==========")
for row in session.query(TicketMessage.message_body).join(
    Ticket, Ticket.ticket_id == TicketMessage.ticket_id
).filter(
    Ticket.account_id == account_id,
    TicketMessage.timestamp >= start_date,
    TicketMessage.timestamp < as_of_date,
).all():
    print("-", row.message_body)

print("\n========== CALL TRANSCRIPTS ==========")
for row in session.query(CallTranscripts.transcript).filter(
    CallTranscripts.account_id == account_id,
    CallTranscripts.date >= start_date,
    CallTranscripts.date < as_of_date,
).all():
    print("-", row.transcript)

print("\n========== MEETING NOTES ==========")
for row in session.query(Meetings.notes).filter(
    Meetings.account_id == account_id,
    Meetings.date >= start_date,
    Meetings.date < as_of_date,
).all():
    print("-", row.notes)

print("\n========== BILLING EVENTS ==========")
for row in session.query(BillingEvents.event_description).filter(
    BillingEvents.account_id == account_id,
    BillingEvents.created_at >= start_date,
    BillingEvents.created_at < as_of_date,
).all():
    print("-", row.event_description)