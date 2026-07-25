from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
load_dotenv()
import os
ACCOUNT_VECTOR_STORE_PATH = "backend/rag/account_faiss_index"
BUSINESS_VECTOR_STORE_PATH = "backend/rag/business_faiss_index"

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY_2")
)


def get_retriever():

    account_vector_store = FAISS.load_local(
        ACCOUNT_VECTOR_STORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    account_retriever = account_vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4},
    )

    business_vector_store = FAISS.load_local(
        BUSINESS_VECTOR_STORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True,
    )

    business_retriever = business_vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2},
    )

    return {
        "account_retriever": account_retriever,
        "business_retriever": business_retriever,
    }