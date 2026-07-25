
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.logger.custom_logger import logger
from backend.RAG.document_builder import (
    build_account_collection,
    build_business_collection,
)

load_dotenv()

ACCOUNT_VECTOR_STORE_PATH = "backend/rag/account_faiss_index"
BUSINESS_VECTOR_STORE_PATH = "backend/rag/business_faiss_index"

embeddings1 = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY_1"),
)

embeddings2 = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY_2"),
)

embeddings3 = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY_3"),
)


def build_vector_store(structured_input, analysis_date):
    """Builds two FAISS vector stores concurrently:

    1. Account Vector Store 2. Business Insight Vector Store

    Existing vector stores are deleted before rebuilding.
    """

    account_documents = build_account_collection(
        structured_input,
        analysis_date,
    )

    business_documents = build_business_collection(
        structured_input,
        analysis_date,
    )

    for path in [
        ACCOUNT_VECTOR_STORE_PATH,
        BUSINESS_VECTOR_STORE_PATH,
    ]:
        if Path(path).exists():
            shutil.rmtree(path)

    total_account_docs = len(account_documents)

    if total_account_docs > 0:
        chunk_size = (total_account_docs + 2) // 3

        part1_docs = account_documents[:chunk_size]
        part2_docs = account_documents[chunk_size : chunk_size * 2]
        part3_docs = account_documents[chunk_size * 2 :]

        logger.info(
            f"Splitting {total_account_docs} account documents across 3 parallel embedders: "
            f"Part 1 ({len(part1_docs)}), Part 2 ({len(part2_docs)}), Part 3 ({len(part3_docs)})."
        )

        workers = [
            (part1_docs, embeddings1),
            (part2_docs, embeddings2),
            (part3_docs, embeddings3),
        ]
        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(
                    FAISS.from_documents,
                    documents=docs,
                    embedding=embed_model,
                )
                for docs, embed_model in workers
                if docs
            ]
            for future in futures:
                res = future.result()
                if res is not None:
                    results.append(res)

        if results:
            account_vector_store = results[0]
            for additional_store in results[1:]:
                account_vector_store.merge_from(additional_store)

            account_vector_store.save_local(ACCOUNT_VECTOR_STORE_PATH)
            logger.info("Account vector store created successfully.")
        else:
            account_vector_store = None
    else:
        account_vector_store = None

    total_business_docs = len(business_documents)

    if total_business_docs > 0:
        chunk_size2 = (total_business_docs + 2) // 3

        part1_docs2 = business_documents[:chunk_size2]
        part2_docs2 = business_documents[chunk_size2 : chunk_size2 * 2]
        part3_docs2 = business_documents[chunk_size2 * 2 :]

        logger.info(
            f"Splitting {total_business_docs} business documents across 3 parallel embedders: "
            f"Part 1 ({len(part1_docs2)}), Part 2 ({len(part2_docs2)}), Part 3 ({len(part3_docs2)})."
        )

        workers2 = [
            (part1_docs2, embeddings1),
            (part2_docs2, embeddings2),
            (part3_docs2, embeddings3),
        ]
        results2 = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures2 = [
                executor.submit(
                    FAISS.from_documents,
                    documents=docs,
                    embedding=embed_model,
                )
                for docs, embed_model in workers2
                if docs
            ]
            for future in futures2:
                res = future.result()
                if res is not None:
                    results2.append(res)

        if results2:
            business_vector_store = results2[0]
            for additional_store in results2[1:]:
                business_vector_store.merge_from(additional_store)

            business_vector_store.save_local(BUSINESS_VECTOR_STORE_PATH)
            logger.info("Business insight vector store created successfully.")
        else:
            business_vector_store = None
    else:
        business_vector_store = None

    return {
        "account_vector_store": account_vector_store,
        "business_vector_store": business_vector_store,
    }