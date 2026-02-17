from os import name
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings

class PineconeClient:
    def __init__(self):
        self.client = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index_name = settings.PINECONE_API_INDEX
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        if self.index_name not in self.client.list_indexes().names():
            self.client.create_index(
                name=self.index_name,
                dimension=3072,  # OpenAI embedding dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.PINECONE_API_ENV
                )
            )
    
    def get_index(self):
        """Get the Pinecone index"""
        return self.client.Index(self.index_name)
    
    def upsert_vectors(self, vectors, namespace="default"):
        """Insert or update vectors in the index"""
        index = self.get_index()
        return index.upsert(vectors=vectors, namespace=namespace)
    
    def query_vectors(self, query_vector, top_k=5, filter_dict=None, namespace="default"):
        """Query for similar vectors"""
        index = self.get_index()
        return index.query(
            vector=query_vector,
            namespace=namespace,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True
        )
    
    def delete_vectors(self, vector_ids):
        """Delete vectors by ID"""
        index = self.get_index()
        return index.delete(ids=vector_ids)

# Global instance
pinecone_client = PineconeClient()