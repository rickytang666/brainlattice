from openai import OpenAI
from core.config import get_settings
from typing import List

settings = get_settings()

class EmbeddingService:
    """embedding service using openai text-embedding-3-small"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "text-embedding-3-small"  # 1536 dimensions

    def get_embedding(self, text: str) -> List[float]:
        """get single vector for text"""
        try:
            # clean text to avoid token issues
            text = text.replace("\n", " ")
            response = self.client.embeddings.create(
                input=[text],
                model=self.model
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"failed to get embedding: {str(e)}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """batch embed multiple texts"""
        try:
            # clean all texts
            cleaned_texts = [t.replace("\n", " ") for t in texts]
            response = self.client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            raise Exception(f"failed to get batch embeddings: {str(e)}")
