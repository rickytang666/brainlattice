import logging
from core.config import get_settings
from typing import List

settings = get_settings()
logger = logging.getLogger(__name__)

class EmbeddingService:
    """embedding service with openai (primary) and gemini (fallback) gracefully supporting 1536 dimensions"""
    
    @staticmethod
    def provider_for(gemini_key: str = None, openai_key: str = None) -> str:
        """which provider these keys select; __init__ uses it too, so the two can't drift"""
        if openai_key:
            return "openai"
        if gemini_key:
            return "gemini"
        raise ValueError("No API key provided for EmbeddingService. Strict BYOK is enabled.")

    def __init__(self, gemini_key: str = None, openai_key: str = None):
        self.dimensions = 1536
        self.provider = self.provider_for(gemini_key=gemini_key, openai_key=openai_key)

        if self.provider == "openai":
            from openai import OpenAI
            self.openai_client = OpenAI(api_key=openai_key)
            self.openai_model = "text-embedding-3-small"
            logger.info("initialized openai embedding service (BYOK custom key)")
        else:
            from google import genai
            self.gemini_client = genai.Client(api_key=gemini_key)
            self.gemini_model = "gemini-embedding-001"
            logger.info("initialized gemini embedding service (BYOK custom key)")

    def get_embedding(self, text: str) -> List[float]:
        """get single vector for text"""
        try:
            # clean text to avoid token issues
            text = text.replace("\n", " ")
            
            if self.provider == "openai":
                response = self.openai_client.embeddings.create(
                    input=[text],
                    model=self.openai_model
                )
                return response.data[0].embedding
            else:
                from google.genai import types
                response = self.gemini_client.models.embed_content(
                    model=self.gemini_model,
                    contents=text,
                    config=types.EmbedContentConfig(output_dimensionality=self.dimensions)
                )
                return response.embeddings[0].values
                
        except Exception as e:
            raise Exception(f"failed to get embedding: {str(e)}")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """batch embed multiple texts"""
        if not texts:
            return []
            
        try:
            # clean all texts
            cleaned_texts = [t.replace("\n", " ") for t in texts]
            
            if self.provider == "openai":
                response = self.openai_client.embeddings.create(
                    input=cleaned_texts,
                    model=self.openai_model
                )
                return [data.embedding for data in response.data]
            else:
                # Gemini embed API: at most 100 contents per batch (OpenAI has a higher limit)
                from google.genai import types
                cfg = types.EmbedContentConfig(output_dimensionality=self.dimensions)
                out: List[List[float]] = []
                batch_size = 100
                for i in range(0, len(cleaned_texts), batch_size):
                    batch = cleaned_texts[i : i + batch_size]
                    response = self.gemini_client.models.embed_content(
                        model=self.gemini_model,
                        contents=batch,
                        config=cfg,
                    )
                    out.extend([data.values for data in response.embeddings])
                return out
                
        except Exception as e:
            raise Exception(f"failed to get batch embeddings: {str(e)}")
