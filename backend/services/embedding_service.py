import logging
from core.config import get_settings
from typing import List

settings = get_settings()
logger = logging.getLogger(__name__)

class EmbeddingService:
    """embedding service with openai (primary) and gemini (fallback) gracefully supporting 1536 dimensions"""
    
    def __init__(self, gemini_key: str = None, openai_key: str = None):
        self.dimensions = 1536
        
        if openai_key:
            from openai import OpenAI
            self.provider = "openai"
            self.openai_client = OpenAI(api_key=openai_key)
            self.openai_model = "text-embedding-3-small"
            logger.info("initialized openai embedding service (BYOK custom key)")
        elif gemini_key:
            from google import genai
            self.provider = "gemini"
            self.gemini_client = genai.Client(api_key=gemini_key)
            self.gemini_model = "text-embedding-004"
            logger.info("initialized gemini embedding service (BYOK custom key)")
        else:
            raise ValueError("No API key provided for EmbeddingService. Strict BYOK is enabled.")

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
                from google.genai import types
                response = self.gemini_client.models.embed_content(
                    model=self.gemini_model,
                    contents=cleaned_texts,
                    config=types.EmbedContentConfig(output_dimensionality=self.dimensions)
                )
                return [data.values for data in response.embeddings]
                
        except Exception as e:
            raise Exception(f"failed to get batch embeddings: {str(e)}")
