from dotenv import load_dotenv
import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
from backend.RAG.retriever import get_retriever
from backend.prompts.chatbot_prompt import chatbot_prompt

load_dotenv()

agent = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    api_key=os.getenv("GOOGLE_API_KEY_2"),
)

chat_history = []

def chatbot(user_question: str):
    retriever = get_retriever()
    account_docs = retriever["account_retriever"].invoke(user_question)
    business_docs = retriever["business_retriever"].invoke(user_question)

    seen = set()
    retrieved_documents = []

    for doc in business_docs + account_docs:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            retrieved_documents.append(doc)

    # for i, doc in enumerate(retrieved_documents, 1):
    #     print(f"\n===== Document {i} =====")
    #     print(doc.metadata)
    #     print(doc.page_content)

    context_parts = []

    for i, doc in enumerate(retrieved_documents, start=1):
        context_parts.append(
            f"""
    ==================== Document {i} ====================

    Content:
    {doc.page_content}

    Metadata:
    {json.dumps(doc.metadata, indent=2, default=str)}

    ======================================================
    """
        )

    context = "\n".join(context_parts)

    prompt = chatbot_prompt.invoke(
        {
            "context": context,
            "chat_history": chat_history,
            "input": user_question,
        }
    )

    response = agent.invoke(prompt)
    chat_history.append(HumanMessage(content=user_question))
    chat_history.append(AIMessage(content=response.content))

    return response.content