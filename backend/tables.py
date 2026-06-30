from sqlalchemy import create_engine, Column, Integer, String,Float,Date,ForeignKey,Boolean,DateTime,Text
from sqlalchemy.orm import sessionmaker,declarative_base,relationship
from pgvector.sqlalchemy import Vector

engine = create_engine("postgresql+psycopg2://postgres:IDF%40y2023@localhost:5433/customer_retention")
Base = declarative_base()

class Account(Base):
    __tablename__ = 'accounts'
    account_id = Column(String,primary_key=True)
    account_name = Column(String,nullable = False)
    industry = Column(String)
    company_size = Column(Integer)
    plan = Column(String)
    contract_value = Column(Float)
    renewal_date = Column(Date)
    account_status = Column(String)
    archetype = Column(String)
    contacts = relationship("Contact", back_populates="account")
    tickets = relationship("Ticket", back_populates="account")
    usage_events = relationship("UsageEvent", back_populates="account")
    subscriptions = relationship("Subscription", back_populates="account")
    invoices = relationship("Invoices", back_populates="account")
    billing_events = relationship("BillingEvents", back_populates="account")
    emails = relationship("Emails", back_populates="account")
    meetings = relationship("Meetings", back_populates="account")
    call_transcripts = relationship("CallTranscripts",back_populates="account")
    csm_notes = relationship("CsmNotes",back_populates="account")
    feedback = relationship("Feedback",back_populates="account")
    outcomes = relationship("Outcomes",back_populates="account")


class Contact(Base):
    __tablename__ = 'contacts'
    contact_id = Column(String,primary_key=True)
    account_id = Column(String,ForeignKey('accounts.account_id'))
    name = Column(String)
    job_title = Column(String)
    email = Column(String)
    decision_maker_flag = Column(Boolean)
    is_primary_contact = Column(Boolean)
    account = relationship("Account", back_populates="contacts")


class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    created_at = Column(DateTime)
    resolved_at = Column(DateTime)

    status = Column(String)
    priority = Column(String)

    subject = Column(String)
    description = Column(Text)
    text_embeddings = Column(Vector(1536))

    account = relationship("Account", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket")

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    message_id = Column(String, primary_key=True)
    ticket_id = Column(String, ForeignKey("tickets.ticket_id"))

    sender_type = Column(String)
    timestamp = Column(DateTime)
    message_body = Column(Text)

    ticket = relationship("Ticket", back_populates="messages")

class UsageEvent(Base):
    __tablename__ = "usage_events"

    event_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    timestamp = Column(DateTime)
    event_name = Column(String)
    account = relationship("Account", back_populates="usage_events")

class Subscription(Base):
    __tablename__ = "subscriptions"

    subscription_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    plan = Column(String)
    contract_value = Column(Float)
    renewal_date = Column(Date)
    status = Column(String)

    account = relationship("Account", back_populates="subscriptions")

class Invoices(Base):
    __tablename__ = "invoices"

    invoice_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    amount = Column(Float)
    due_date = Column(Date)
    status = Column(String)

    account = relationship("Account", back_populates="invoices")
    billing_events = relationship("BillingEvents", back_populates="invoice")

class BillingEvents(Base):
    __tablename__ = "billing_events"

    event_id = Column(String, primary_key=True)

    account_id = Column(String, ForeignKey("accounts.account_id"))
    invoice_id = Column(String, ForeignKey("invoices.invoice_id"))

    event_type = Column(String)
    event_description = Column(String)
    created_at = Column(DateTime)

    account = relationship("Account", back_populates="billing_events")
    invoice = relationship("Invoices", back_populates="billing_events")

class Emails(Base):
    __tablename__ = "emails"

    email_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    timestamp = Column(DateTime)
    subject = Column(String)
    body = Column(Text)

    account = relationship("Account", back_populates="emails")

class Meetings(Base):
    __tablename__ = "meetings"

    meeting_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    date = Column(Date)
    notes = Column(Text)

    account = relationship("Account", back_populates="meetings")

class CallTranscripts(Base):
    __tablename__ = "call_transcripts"
    call_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))
    date = Column(Date)
    transcript = Column(Text)
    account = relationship("Account", back_populates="call_transcripts")

class CsmNotes(Base):
    __tablename__ = "csm_notes"

    note_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    created_at = Column(DateTime)
    note = Column(Text)

    account = relationship("Account", back_populates="csm_notes")
    
class Feedback(Base):
    __tablename__ = "feedback"

    feedback_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    query = Column(String)
    recommended_action = Column(String)
    feedback = Column(Text)
    timestamp = Column(DateTime)
    account = relationship("Account", back_populates="feedback")

class Outcomes(Base):
    __tablename__ = "outcomes"

    outcome_id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("accounts.account_id"))

    action_taken = Column(String)
    outcome_type = Column(String)
    outcome_date = Column(Date)

    account = relationship("Account", back_populates="outcomes")


Base.metadata.create_all(engine)