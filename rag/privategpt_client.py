#!/usr/bin/env python3
"""
Private-GPT Client Wrapper
Enhanced client for interacting with Private-GPT API for email RAG
"""

import requests
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PrivateGPTClient:
    """Enhanced client for interacting with Private-GPT API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
    
    def health_check(self) -> bool:
        """Check if Private-GPT is running."""
        try:
            response = self.session.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def ingest_file(self, file_path: Path, metadata: Dict[str, Any]) -> str:
        """Ingest a file into Private-GPT."""
        try:
            # Upload file
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'text/plain')}
                response = self.session.post(
                    f"{self.base_url}/v1/ingest/file",
                    files=files
                )
            
            if response.status_code == 200:
                result = response.json()
                file_id = result.get('id')
                
                # Update metadata
                if file_id:
                    self.update_metadata(file_id, metadata)
                
                return file_id
            else:
                raise Exception(f"Ingestion failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Error ingesting file {file_path}: {e}")
            raise
    
    def query(self, question: str, collection_id: str = None, 
              top_k: int = 5, filter_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Query Private-GPT with a question."""
        try:
            payload = {
                "query": question,
                "top_k": top_k,
                "collection_id": collection_id,
                "filter_metadata": filter_metadata or {}
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Query failed: {response.text}")
                
        except Exception as e:
            logger.error(f"Error querying Private-GPT: {e}")
            raise
    
    def update_metadata(self, file_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for an ingested file."""
        try:
            response = self.session.put(
                f"{self.base_url}/v1/ingest/{file_id}/metadata",
                json=metadata
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error updating metadata: {e}")
            return False
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Private-GPT."""
        try:
            response = self.session.delete(f"{self.base_url}/v1/ingest/{file_id}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        try:
            response = self.session.get(f"{self.base_url}/v1/ingest/list")
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            response = self.session.get(f"{self.base_url}/v1/ingest/stats")
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {} 