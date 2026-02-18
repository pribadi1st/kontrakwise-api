import time
from google import genai
from app.core.config import settings

from typing import List

class GeminiAI:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model = "gemini-embedding-001"
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embedding for a single text"""
        try:
            response = self.client.models.embed_content(contents=text, model=self.model)
            return response.embeddings[0].values
        except Exception as e:
            raise Exception(f"Failed to create embedding: {str(e)}")
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for multiple texts (batch processing)"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            raise Exception(f"Failed to create embeddings: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model"""
        return 1536  # text-embedding-3-small dimension

    def generate_content(self, prompt: str) -> str:
        """Generate content using Gemini"""
        max_retries = 3
        retry_delay = 1 # seconds
        
        for attempt in range(max_retries):
            try:
                print(f"Generating content for prompt")
                response = self.client.models.generate_content(
                    model="gemini-3-flash-preview",
                    contents=prompt
                )
                
                return response.text
                
            except Exception as e:
                print(f"Error generating content: {str(e), type(e)}")
                if attempt < max_retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                raise Exception(f"Failed to generate AI response: {str(e)}")
    
    def generate_content_stream(self, prompt: str):
        """Generate streaming content using Gemini"""
        try:
            print(f"Starting streaming content generation")
            response = self.client.models.generate_content_stream(
                model="gemini-3-flash-preview",
                contents=prompt
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            print(f"Error in streaming content generation: {str(e)}")
            raise Exception(f"Failed to generate streaming AI response: {str(e)}")

# Global instance
gemAI = GeminiAI()
