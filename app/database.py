import os
import uuid
import asyncio
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings
from app.models import Event

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            check_compatibility=False  # Add this line
        )
        self.collection_name = "fraud_events"
        self.embeddings = OpenAIEmbeddings()
        self._setup_collection()
    
    def _setup_collection(self):
        """Create collection if it doesn't exist"""
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536,  # OpenAI embedding size
                    distance=models.Distance.COSINE
                )
            )
    
    async def add_event(self, event: Event):
        """Add event to vector store"""
        try:
            # Create searchable text
            text = f"Event: {event.event_type} Account: {event.account_id} IP: {event.ip_address}"
            
            # Generate embedding
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self.embeddings.embed_query, text
            )
            
            # Create point
            point = models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "account_id": event.account_id or "unknown",
                    "ip_address": event.ip_address or "unknown",
                    "risk_score": event.risk_score or 0.0,
                    "timestamp": event.timestamp.isoformat(),
                    "text": text
                }
            )
            
            # Insert
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
            )
            
        except Exception as e:
            print(f"Error adding event to vector store: {e}")
    
    async def search_similar(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for similar events"""
        try:
            # Generate query embedding
            embedding = await asyncio.get_event_loop().run_in_executor(
                None, self.embeddings.embed_query, query
            )
            
            # Search
            results = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.search(
                    collection_name=self.collection_name,
                    query_vector=embedding,
                    limit=limit,
                    with_payload=True
                )
            )
            
            return [hit.payload for hit in results]
            
        except Exception as e:
            print(f"Error searching vector store: {e}")
            return []