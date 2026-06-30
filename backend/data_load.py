import json
from tables import *
from sqlalchemy.orm import sessionmaker

Session = sessionmaker(bind=engine)
session = Session()

with open("b2b_customer_dataset.json", "r") as f:
    data = json.load(f)

table_map = {
    "accounts": Account,
    "contacts": Contact,
    "tickets": Ticket,
    "ticket_messages": TicketMessage,
    "usage_events": UsageEvent,
    "subscriptions": Subscription,
    "invoices": Invoices,
    "billing_events": BillingEvents,
    "emails": Emails,
    "meetings": Meetings,
    "call_transcripts": CallTranscripts,
    "csm_notes": CsmNotes,
    "feedback": Feedback,
    "outcomes": Outcomes,
}

for key, model in table_map.items():
    for row in data[key]:
        session.add(model(**row))

session.commit()
