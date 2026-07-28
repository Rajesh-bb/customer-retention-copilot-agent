import os
import requests

from langchain_core.embeddings import Embeddings


class OpenRouterEmbeddings(Embeddings):
    def __init__(
        self,
        model: str = "nvidia/nemotron-3-embed-1b:free",
        api_key: str | None = None,
    ):
        self.model = model
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        if self.api_key is None:
            raise ValueError("OPENROUTER_API_KEY not found.")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        response = requests.post(
            "https://openrouter.ai/api/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": texts,
                "encoding_format": "float",
            },
            timeout=120,
        )

        response.raise_for_status()

        data = response.json()

        return [
            item["embedding"]
            for item in data["data"]
        ]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]