from backend.recommendation.recommendation import State
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from backend.prompts.rag_prompt import business_insight_prompt
from backend.logger.custom_logger import logger
import json
from backend.customer_intelligence_agent.analyst import get_info
from dotenv import load_dotenv
import os
load_dotenv()

structured_input = State["structured_input"]




def build_account_collection(structured_input, input_date):

    documents = []

    # Get all raw CRM data once
    raw_accounts = get_info(structured_input, input_date)

    raw_lookup = {
        account["account_id"]: account
        for account in raw_accounts
    }

    for account in structured_input:

        account_id = account["account_id"]

        raw = raw_lookup.get(account_id, {})
        csm_notes = "\n".join(raw.get("csm", []))
        emails = "\n".join(raw.get("emails", []))
        tickets = "\n".join(raw.get("tickets", []))
        ticket_messages = "\n".join(raw.get("ticket_messages", []))
        meetings = "\n".join(raw.get("meetings", []))
        call_transcripts = "\n".join(raw.get("call_transcripts", []))
        billings = "\n".join(raw.get("billings", []))

        page_content = f"""
    ==============================
    CUSTOMER ACCOUNT
    ==============================

    Account ID:
    {account_id}

    Industry:
    {account["meta_data"]["industry"]}

    Plan:
    {account["meta_data"]["plan"]}

    Company Size:
    {account["meta_data"]["company_size"]}

    Contract Value:
    {account["meta_data"]["contract_value"]}

    Renewal Date:
    {account["meta_data"]["renewal_date"]}

    Archetype:
    {account["meta_data"]["archetype"]}

    ==================================================
    ACCOUNT SUMMARY
    ==================================================

    {account["summary"]}

    ==================================================
    CSM NOTES
    ==================================================

    {csm_notes}

    ==================================================
    EMAILS
    ==================================================

    {emails}

    ==================================================
    SUPPORT TICKETS
    ==================================================

    {tickets}

    ==================================================
    TICKET MESSAGES
    ==================================================

    {ticket_messages}

    ==================================================
    MEETING NOTES
    ==================================================

    {meetings}

    ==================================================
    CALL TRANSCRIPTS
    ==================================================

    {call_transcripts}

    ==================================================
    BILLING EVENTS
    ==================================================

    {billings}
    """

        doc = Document(
            page_content=page_content,
            metadata={
                "type": "account",
                "account_id": account_id,
                "renewal_date": account["meta_data"]["renewal_date"],
                "plan": account["meta_data"]["plan"],
                "industry": account["meta_data"]["industry"],
                "company_size": account["meta_data"]["company_size"],
                "contract_value": account["meta_data"]["contract_value"],
                "archetype": account["meta_data"]["archetype"],
            },
        )

        documents.append(doc)

    return documents

agent = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key= os.getenv("GOOGLE_API_KEY_1")
)



def build_business_collection(
    structured_input: list[dict],
    input_date,
) -> list[Document]:

    # Retrieve the raw CRM evidence for all accounts
    raw_accounts = get_info(structured_input, input_date)

    prompt = business_insight_prompt.invoke(
        {
            "input": raw_accounts
        }
    )

    response = agent.invoke(prompt)

    insights = json.loads(response.content[0]["text"])

    documents = []

    for insight in insights:

        doc = Document(
            page_content=f"""
==================================================
DOCUMENT TYPE
==================================================

Business Insight

==================================================
TITLE
==================================================

{insight["title"]}

==================================================
CONTENT
==================================================

{insight["content"]}
""",
            metadata={
                "type": "business_insight",
                "title": insight["title"],
            },
        )

        documents.append(doc)

    logger.info("generated business insights")

    return documents


