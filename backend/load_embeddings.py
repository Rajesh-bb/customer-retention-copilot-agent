import json
from sqlalchemy.orm import sessionmaker
from tables import *

Session = sessionmaker(bind = engine)
session = Session()

with open("tickets.json","r") as f:
    data = json.load(f)

for x in data:
    ticket_id = x["ticket_id"]
    q = session.query(Ticket).filter(Ticket.ticket_id == ticket_id).one()
    embedding = json.loads(x["embedding"])
    q.text_embeddings = embedding
    session.add(q)
session.commit()