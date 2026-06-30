from backend.customer_intelligence_agent.healthscore import session
from tables import Ticket, TicketMessage

result = (
    session.query(TicketMessage.message_body, Ticket.description)
    .join(Ticket, Ticket.ticket_id == TicketMessage.ticket_id)
    .limit(3)
    .all()
)

print(result)

for row in result:
    print(row)
    print(row.message_body)
    print(row.description)