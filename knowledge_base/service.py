import json
import logging
import redis
from typing import List, Optional
from datetime import datetime
from markupsafe import escape          # ← NEW: prevents Jinja syntax errors

from .models import KnowledgeBaseEntry
from config import Config

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or Config.REDIS_URL
        self.redis = redis.from_url(self.redis_url, decode_responses=True)
    
    async def add_entry(self, question: str, answer: str, source: str = "supervisor") -> KnowledgeBaseEntry:
        # --- ESCAPE USER TEXT BEFORE STORAGE -----------------------------
        question = escape(question)
        answer   = escape(answer)
        # -----------------------------------------------------------------
        
        entry = KnowledgeBaseEntry(question, answer, source)
        
        key = f"knowledge:{entry.id}"
        self.redis.set(key, json.dumps(entry.to_dict()))
        
        self.redis.sadd("knowledge:index", key)
        
        logger.info(f"Added knowledge base entry: {entry.id}")
        return entry
    
    async def find_answer(self, question: str) -> Optional[str]:
        normalized_question = self._normalize_question(question)
        
        index_keys = self.redis.smembers("knowledge:index")
        if not index_keys:
            return None
        
        for key in index_keys:
            data = self.redis.get(key)
            if data:
                try:
                    entry_data = json.loads(data)
                    if entry_data.get("question") == normalized_question:
                        # Update usage
                        entry_data["usage_count"] = entry_data.get("usage_count", 0) + 1
                        entry_data["last_used"] = datetime.utcnow().isoformat()
                        self.redis.set(key, json.dumps(entry_data))
                        return entry_data["answer"]
                except Exception as e:
                    logger.warning(f"Error reading KB entry {key}: {e}")
                    continue
        
        return None
    
    async def get_all_entries(self) -> List[KnowledgeBaseEntry]:
        entries = []
        
        try:
            index_keys = self.redis.smembers("knowledge:index")
            
            if not index_keys:
                return entries
            
            for key in index_keys:
                try:
                    data = self.redis.get(key)
                    if data:
                        entry_data = json.loads(data)
                        entry = self._dict_to_kb_entry(entry_data)
                        entries.append(entry)
                except Exception as e:
                    logger.warning(f"Skipping invalid KB entry {key}: {e}")
                    continue
            
            return sorted(entries, key=lambda x: x.last_used, reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting knowledge entries: {e}")
            return []
    
    async def delete_entry(self, entry_id: str) -> bool:
        key = f"knowledge:{entry_id}"
        try:
            result = self.redis.delete(key)
            self.redis.srem("knowledge:index", key)
            return bool(result)
        except Exception as e:
            logger.error(f"Error deleting entry {entry_id}: {e}")
            return False
    
    def _normalize_question(self, question: str) -> str:
        if not question:
            return ""
        return question.lower().strip()
    
    def _dict_to_kb_entry(self, data: dict) -> KnowledgeBaseEntry:
        try:
            # Safe datetime parsing
            created_at = datetime.utcnow()
            last_used = datetime.utcnow()
            
            if "created_at" in data and data["created_at"]:
                try:
                    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                except:
                    created_at = datetime.utcnow()
            
            if "last_used" in data and data["last_used"]:
                try:
                    last_used = datetime.fromisoformat(data["last_used"].replace("Z", "+00:00"))
                except:
                    last_used = created_at
            
            return KnowledgeBaseEntry(
                question=data.get("question", ""),
                answer=data.get("answer", ""),
                source=data.get("source", "unknown"),
                id=data.get("id"),
                created_at=created_at,
                usage_count=data.get("usage_count", 0),
                last_used=last_used
            )
        except Exception as e:
            logger.error(f"Error converting dict to KB entry: {e}")
            return KnowledgeBaseEntry(
                question="Error",
                answer="Error loading entry",
                source="error"
            )