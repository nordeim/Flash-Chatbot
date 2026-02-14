

# Re-Imagining Memory: A System Design for Persistent User Context

## The Core Problem — Stated Precisely

Every `st.rerun()` or browser refresh resets the chatbot to a blank slate. The user's name, expertise, preferences, ongoing projects, communication style — all evaporate. This creates **conversational amnesia**: the user must re-establish context every session. The cognitive tax is real, and it's the primary reason chatbot interactions feel transactional rather than relational.

The goal: **make the chatbot feel like a colleague who took notes**, not a stranger reading a script.

---

## Phase 0: Psychological & UX Analysis

Before architecting anything, I need to understand what "not a stranger" actually means cognitively.

### What Makes a Conversation Feel "Known"?

| Signal | Example | Memory Type Required |
|---|---|---|
| **Name recognition** | "Welcome back, Alex" | Semantic fact |
| **Context continuity** | "How did the Django deployment go?" | Episodic recall |
| **Style adaptation** | Concise answers for experts, detailed for beginners | Procedural/behavioral |
| **Preference respect** | Uses TypeScript in examples without being asked | Semantic preference |
| **Topic threading** | "This relates to the auth system you built last week" | Episodic + semantic linking |
| **Proactive awareness** | "Since you're using Next.js 15, note this breaking change" | Semantic + inference |
| **Emotional calibration** | Matches energy level — brief when user is terse, detailed when curious | Behavioral observation |

### The Uncanny Valley of Memory

Too little memory → stranger. Too much memory → surveillance. The sweet spot:

```
CREEPY:  "I noticed you always chat between 2-4am, is everything okay?"
WARM:    "Last time you mentioned migrating to Next.js — how's that going?"
NATURAL: Uses TypeScript in code examples because it learned you prefer it.
IDEAL:   Doesn't mention memory at all — just behaves like it knows you.
```

**Design principle:** Memory should be **invisible in execution, visible in control**. The user feels known without feeling watched. But they can inspect, edit, and delete everything.

---

## Phase 1: Memory Taxonomy

Drawing from cognitive science, I propose four memory layers:

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MEMORY ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    Stable, factual, long-lived                   │
│  │   SEMANTIC    │    "User is a senior Python developer"           │
│  │   MEMORY      │    "User's name is Alex"                        │
│  │              │    "User works at a fintech startup"              │
│  └──────┬───────┘                                                   │
│         │                                                           │
│  ┌──────▼───────┐    Conversation-level summaries                  │
│  │   EPISODIC   │    "2025-07-11: Discussed CORS debugging"        │
│  │   MEMORY      │    "2025-07-09: Built a FastAPI auth system"    │
│  │              │    Timestamped, searchable, fadeable              │
│  └──────┬───────┘                                                   │
│         │                                                           │
│  ┌──────▼───────┐    How the user likes to interact                │
│  │  PROCEDURAL  │    "Prefers code-first explanations"             │
│  │   MEMORY      │    "Likes concise answers, dislikes fluff"      │
│  │              │    "Wants TypeScript, not JavaScript"             │
│  └──────┬───────┘                                                   │
│         │                                                           │
│  ┌──────▼───────┐    Current session (already exists)              │
│  │   WORKING    │    The conversation history in session_state     │
│  │   MEMORY      │    Ephemeral, cleared on "New Chat"             │
│  └──────────────┘                                                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Taxonomy?

- **Semantic** memories are cheap to inject (small, stable) and high-impact (personalization).
- **Episodic** memories enable cross-session threading ("last time we discussed...").
- **Procedural** memories shape *how* the model responds, not *what* it knows.
- **Working** memory is the current conversation — already implemented.

---

## Phase 2: Technical Architecture

### 2.1 Data Models

```python
# src/memory/models.py

"""Memory system data models."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict


class MemoryCategory(str, Enum):
    """Categories of persistent memory."""
    FACT = "fact"               # "User is a backend developer"
    PREFERENCE = "preference"   # "Prefers Python over Java"
    TOPIC = "topic"             # "Working on e-commerce migration"
    STYLE = "style"             # "Likes concise answers"
    SUMMARY = "summary"         # "Conversation about Docker setup"


class MemoryPriority(str, Enum):
    """Priority levels for memory injection."""
    CORE = "core"       # Always inject (name, role)
    HIGH = "high"       # Inject when relevant or space allows
    NORMAL = "normal"   # Inject only when semantically relevant
    LOW = "low"         # Only on direct recall


@dataclass
class MemoryEntry:
    """A single memory unit."""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    category: MemoryCategory = MemoryCategory.FACT
    content: str = ""
    priority: MemoryPriority = MemoryPriority.NORMAL
    confidence: float = 0.8          # 0.0–1.0, extraction confidence
    source_session_id: str = ""      # Which conversation spawned this
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_accessed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    access_count: int = 0
    superseded_by: Optional[str] = None  # ID of newer contradicting memory
    active: bool = True
    
    def touch(self) -> None:
        """Mark memory as accessed."""
        self.last_accessed_at = datetime.now(timezone.utc).isoformat()
        self.access_count += 1
    
    def deactivate(self, superseded_by: Optional[str] = None) -> None:
        """Soft-delete: mark inactive but preserve for audit."""
        self.active = False
        self.superseded_by = superseded_by
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Deserialize from dictionary."""
        # Convert string enums back
        if isinstance(data.get("category"), str):
            data["category"] = MemoryCategory(data["category"])
        if isinstance(data.get("priority"), str):
            data["priority"] = MemoryPriority(data["priority"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class UserProfile:
    """Aggregated user profile from all memories."""
    
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    display_name: Optional[str] = None
    memories: List[MemoryEntry] = field(default_factory=list)
    memory_enabled: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_active_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    
    @property
    def active_memories(self) -> List[MemoryEntry]:
        """Only non-superseded, active memories."""
        return [m for m in self.memories if m.active]
    
    @property
    def facts(self) -> List[MemoryEntry]:
        return [m for m in self.active_memories if m.category == MemoryCategory.FACT]
    
    @property
    def preferences(self) -> List[MemoryEntry]:
        return [m for m in self.active_memories if m.category == MemoryCategory.PREFERENCE]
    
    @property
    def topics(self) -> List[MemoryEntry]:
        return [m for m in self.active_memories if m.category == MemoryCategory.TOPIC]
    
    @property
    def style_notes(self) -> List[MemoryEntry]:
        return [m for m in self.active_memories if m.category == MemoryCategory.STYLE]
    
    @property
    def summaries(self) -> List[MemoryEntry]:
        return [m for m in self.active_memories if m.category == MemoryCategory.SUMMARY]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "memories": [m.to_dict() for m in self.memories],
            "memory_enabled": self.memory_enabled,
            "created_at": self.created_at,
            "last_active_at": self.last_active_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        memories = [MemoryEntry.from_dict(m) for m in data.get("memories", [])]
        return cls(
            user_id=data.get("user_id", str(uuid.uuid4())),
            display_name=data.get("display_name"),
            memories=memories,
            memory_enabled=data.get("memory_enabled", True),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            last_active_at=data.get("last_active_at", datetime.now(timezone.utc).isoformat()),
        )
```

### 2.2 Memory Store — Storage-Agnostic with JSON Implementation

```python
# src/memory/store.py

"""Memory persistence layer with pluggable backends."""

import json
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any

from src.memory.models import MemoryEntry, UserProfile, MemoryCategory
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryStore(ABC):
    """Abstract base for memory persistence."""
    
    @abstractmethod
    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load user profile from storage."""
        ...
    
    @abstractmethod
    def save_profile(self, profile: UserProfile) -> None:
        """Persist user profile."""
        ...
    
    @abstractmethod
    def add_memory(self, user_id: str, entry: MemoryEntry) -> None:
        """Add a single memory entry."""
        ...
    
    @abstractmethod
    def remove_memory(self, user_id: str, memory_id: str) -> bool:
        """Remove (soft-delete) a memory entry."""
        ...
    
    @abstractmethod
    def clear_all(self, user_id: str) -> None:
        """Remove all memories for a user."""
        ...
    
    @abstractmethod
    def list_users(self) -> List[str]:
        """List all user IDs with stored profiles."""
        ...


class JSONMemoryStore(MemoryStore):
    """File-based JSON storage — one file per user.
    
    Structure:
        {base_dir}/
            {user_id_hash}.json
    
    Thread-safe via locking. Atomic writes via temp file + rename.
    """
    
    def __init__(self, base_dir: str = "data/memories"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        logger.info(f"JSONMemoryStore initialized at {self.base_dir}")
    
    def _user_path(self, user_id: str) -> Path:
        """Get file path for user, using safe filename."""
        # Hash to avoid filesystem issues with special chars
        import hashlib
        safe_name = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        return self.base_dir / f"{safe_name}.json"
    
    def load_profile(self, user_id: str) -> Optional[UserProfile]:
        path = self._user_path(user_id)
        if not path.exists():
            return None
        
        with self._lock:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                profile = UserProfile.from_dict(data)
                logger.debug(f"Loaded profile for {user_id}: {len(profile.memories)} memories")
                return profile
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Corrupted profile for {user_id}: {e}")
                return None
    
    def save_profile(self, profile: UserProfile) -> None:
        path = self._user_path(profile.user_id)
        temp_path = path.with_suffix(".tmp")
        
        with self._lock:
            try:
                temp_path.write_text(
                    json.dumps(profile.to_dict(), indent=2, ensure_ascii=False),
                    encoding="utf-8"
                )
                temp_path.replace(path)  # Atomic on POSIX
                logger.debug(f"Saved profile for {profile.user_id}")
            except Exception as e:
                logger.error(f"Failed to save profile: {e}")
                if temp_path.exists():
                    temp_path.unlink()
                raise
    
    def add_memory(self, user_id: str, entry: MemoryEntry) -> None:
        profile = self.load_profile(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
        
        profile.memories.append(entry)
        self.save_profile(profile)
    
    def remove_memory(self, user_id: str, memory_id: str) -> bool:
        profile = self.load_profile(user_id)
        if profile is None:
            return False
        
        for memory in profile.memories:
            if memory.id == memory_id:
                memory.deactivate()
                self.save_profile(profile)
                return True
        return False
    
    def clear_all(self, user_id: str) -> None:
        path = self._user_path(user_id)
        with self._lock:
            if path.exists():
                path.unlink()
                logger.info(f"Cleared all memories for {user_id}")
    
    def list_users(self) -> List[str]:
        """List user files (returns hashed IDs — not reversible)."""
        return [p.stem for p in self.base_dir.glob("*.json")]
```

### 2.3 Memory Extractor — The Intelligence Layer

This is the most critical component. It transforms raw conversations into structured memories.

```python
# src/memory/extractor.py

"""Extract structured memories from conversations using LLM + heuristics."""

import json
import re
from typing import List, Dict, Any, Optional, Tuple

from src.memory.models import MemoryEntry, MemoryCategory, MemoryPriority
from src.api.nvidia_client import NvidiaChatClient
from src.api.models import Message
from src.utils.logger import get_logger

logger = get_logger(__name__)


# --- Extraction Prompt ---
# This prompt is carefully designed to produce reliable JSON output.
# It constrains the model to extract only what's explicitly stated or
# strongly implied, with calibrated confidence scores.

EXTRACTION_SYSTEM_PROMPT = """You are a memory extraction system. Your job is to analyze a conversation and extract durable, reusable facts about the USER (not the assistant).

Rules:
1. Extract ONLY information the user explicitly stated or strongly implied.
2. Do NOT infer personality traits from thin evidence.
3. Do NOT extract information about the assistant.
4. Do NOT extract ephemeral/one-time information (e.g., "user said hello").
5. Set confidence: 1.0 = explicitly stated, 0.7 = strongly implied, 0.4 = weakly implied.
6. For preferences, distinguish between stated preferences and observed patterns.
7. Keep each memory to ONE concise sentence.
8. If the conversation is trivial/greeting-only, return empty arrays.

Respond with ONLY valid JSON (no markdown, no explanation):
{
  "facts": [
    {"content": "...", "confidence": 0.0}
  ],
  "preferences": [
    {"content": "...", "confidence": 0.0}
  ],
  "topics_discussed": [
    {"content": "brief topic description", "confidence": 0.0}
  ],
  "communication_style": [
    {"content": "observed style trait", "confidence": 0.0}
  ],
  "summary": "One sentence summarizing the conversation from the user's perspective",
  "user_name": null
}"""


EXTRACTION_USER_TEMPLATE = """Analyze this conversation and extract memories about the user.

CONVERSATION:
{conversation}

Remember: Return ONLY valid JSON. Extract only durable, reusable information."""


class MemoryExtractor:
    """Extracts structured memories from conversation history."""
    
    # Minimum conversation length worth extracting from
    MIN_MESSAGES_FOR_EXTRACTION = 2  # At least one exchange
    
    # Minimum confidence to keep an extraction
    MIN_CONFIDENCE_THRESHOLD = 0.5
    
    def __init__(self, client: Optional[NvidiaChatClient] = None):
        """Initialize extractor.
        
        Args:
            client: NVIDIA API client (created if not provided)
        """
        self.client = client or NvidiaChatClient()
    
    def extract_from_conversation(
        self,
        messages: List[Dict[str, Any]],
        session_id: str = ""
    ) -> List[MemoryEntry]:
        """Extract memories from a conversation.
        
        Uses a two-phase approach:
        1. Rule-based extraction for high-confidence patterns
        2. LLM-based extraction for nuanced understanding
        
        Args:
            messages: Conversation history (list of {role, content} dicts)
            session_id: Session identifier for provenance tracking
            
        Returns:
            List of extracted MemoryEntry objects
        """
        if len(messages) < self.MIN_MESSAGES_FOR_EXTRACTION:
            logger.debug("Conversation too short for extraction")
            return []
        
        # Phase 1: Rule-based extraction (fast, free, high-confidence)
        rule_memories = self._extract_by_rules(messages, session_id)
        
        # Phase 2: LLM-based extraction (slower, richer)
        llm_memories = self._extract_by_llm(messages, session_id)
        
        # Merge and deduplicate
        all_memories = self._merge_memories(rule_memories, llm_memories)
        
        logger.info(
            f"Extracted {len(all_memories)} memories "
            f"(rules: {len(rule_memories)}, llm: {len(llm_memories)})"
        )
        
        return all_memories
    
    def _extract_by_rules(
        self,
        messages: List[Dict[str, Any]],
        session_id: str
    ) -> List[MemoryEntry]:
        """Fast rule-based extraction for obvious patterns.
        
        Catches: name introductions, explicit preferences, language mentions.
        """
        memories = []
        
        # Only scan user messages
        user_messages = [
            m["content"] for m in messages 
            if m.get("role") == "user" and m.get("content")
        ]
        
        full_text = " ".join(user_messages).lower()
        original_text = " ".join(user_messages)
        
        # --- Name Detection ---
        name_patterns = [
            r"(?:my name is|i'm|i am|call me|this is)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            r"^(?:hi|hello|hey),?\s+i'm\s+([A-Z][a-z]+)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, original_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 1 and len(name) < 30:
                    memories.append(MemoryEntry(
                        category=MemoryCategory.FACT,
                        content=f"User's name is {name}",
                        priority=MemoryPriority.CORE,
                        confidence=0.95,
                        source_session_id=session_id,
                    ))
                    break
        
        # --- Explicit Preference Detection ---
        pref_patterns = [
            (r"i (?:prefer|like|love|enjoy|use|always use)\s+(.+?)(?:\.|,|$|!|\?|because|over|instead)", 0.85),
            (r"i (?:hate|dislike|avoid|don't like|never use)\s+(.+?)(?:\.|,|$|!|\?)", 0.80),
        ]
        for pattern, confidence in pref_patterns:
            for match in re.finditer(pattern, full_text):
                pref = match.group(1).strip()
                if 3 < len(pref) < 100:
                    memories.append(MemoryEntry(
                        category=MemoryCategory.PREFERENCE,
                        content=f"User {match.group(0).strip()}",
                        priority=MemoryPriority.HIGH,
                        confidence=confidence,
                        source_session_id=session_id,
                    ))
        
        # --- Role/Job Detection ---
        role_patterns = [
            r"i(?:'m| am) (?:a |an |the )?(.+?(?:developer|engineer|designer|manager|student|researcher|scientist|analyst|architect|lead|founder|cto|ceo))",
            r"i work (?:as|at|for|in)\s+(.+?)(?:\.|,|$)",
        ]
        for pattern in role_patterns:
            match = re.search(pattern, full_text)
            if match:
                role_info = match.group(1).strip()
                if len(role_info) < 80:
                    memories.append(MemoryEntry(
                        category=MemoryCategory.FACT,
                        content=f"User is a {role_info}" if "work" not in match.group(0) else f"User works {match.group(0).strip()[2:]}",
                        priority=MemoryPriority.CORE,
                        confidence=0.9,
                        source_session_id=session_id,
                    ))
                    break
        
        # --- Programming Language Detection ---
        lang_keywords = {
            "python": "Python", "javascript": "JavaScript", "typescript": "TypeScript",
            "rust": "Rust", "go ": "Go", "golang": "Go", "java ": "Java",
            "ruby": "Ruby", "php": "PHP", "swift": "Swift", "kotlin": "Kotlin",
            "c++": "C++", "c#": "C#", "scala": "Scala", "elixir": "Elixir",
        }
        detected_langs = []
        for keyword, name in lang_keywords.items():
            if keyword in full_text:
                detected_langs.append(name)
        
        if detected_langs and len(detected_langs) <= 4:
            memories.append(MemoryEntry(
                category=MemoryCategory.FACT,
                content=f"User works with {', '.join(detected_langs)}",
                priority=MemoryPriority.NORMAL,
                confidence=0.6,  # Lower — could be asking about, not using
                source_session_id=session_id,
            ))
        
        return memories
    
    def _extract_by_llm(
        self,
        messages: List[Dict[str, Any]],
        session_id: str
    ) -> List[MemoryEntry]:
        """LLM-based extraction for nuanced understanding."""
        
        # Format conversation for the extraction prompt
        conversation_text = self._format_conversation(messages)
        
        # Truncate if too long (keep last ~4000 chars)
        if len(conversation_text) > 4000:
            conversation_text = "...\n" + conversation_text[-4000:]
        
        extraction_prompt = EXTRACTION_USER_TEMPLATE.format(
            conversation=conversation_text
        )
        
        try:
            api_messages = [
                Message(role="system", content=EXTRACTION_SYSTEM_PROMPT),
                Message(role="user", content=extraction_prompt),
            ]
            
            response = self.client.chat_complete(
                messages=api_messages,
                max_tokens=1024,
                temperature=0.1,  # Low temperature for consistent extraction
                thinking=False,    # No reasoning needed
            )
            
            if not response.choices or not response.choices[0].message:
                logger.warning("Empty extraction response")
                return []
            
            raw_text = response.choices[0].message.content
            return self._parse_extraction_response(raw_text, session_id)
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fail gracefully — rule-based memories still apply
            return []
    
    def _parse_extraction_response(
        self,
        raw_text: str,
        session_id: str
    ) -> List[MemoryEntry]:
        """Parse LLM extraction response into MemoryEntry objects.
        
        Handles common JSON formatting issues (markdown fences, trailing commas).
        """
        memories = []
        
        # Clean common formatting issues
        text = raw_text.strip()
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        # Remove trailing commas before closing brackets (invalid JSON)
        text = re.sub(r',\s*([}\]])', r'\1', text)
        
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse extraction JSON: {e}\nRaw: {text[:200]}")
            return []
        
        # Category mapping
        category_map = {
            "facts": (MemoryCategory.FACT, MemoryPriority.HIGH),
            "preferences": (MemoryCategory.PREFERENCE, MemoryPriority.HIGH),
            "topics_discussed": (MemoryCategory.TOPIC, MemoryPriority.NORMAL),
            "communication_style": (MemoryCategory.STYLE, MemoryPriority.NORMAL),
        }
        
        for key, (category, default_priority) in category_map.items():
            items = data.get(key, [])
            if not isinstance(items, list):
                continue
            
            for item in items:
                if not isinstance(item, dict) or "content" not in item:
                    continue
                
                content = str(item["content"]).strip()
                confidence = float(item.get("confidence", 0.7))
                
                # Filter low-confidence extractions
                if confidence < self.MIN_CONFIDENCE_THRESHOLD:
                    continue
                
                # Filter empty or too-short content
                if len(content) < 5:
                    continue
                
                memories.append(MemoryEntry(
                    category=category,
                    content=content,
                    priority=default_priority,
                    confidence=confidence,
                    source_session_id=session_id,
                ))
        
        # Handle summary
        summary = data.get("summary")
        if summary and isinstance(summary, str) and len(summary) > 10:
            memories.append(MemoryEntry(
                category=MemoryCategory.SUMMARY,
                content=summary.strip(),
                priority=MemoryPriority.NORMAL,
                confidence=0.9,
                source_session_id=session_id,
            ))
        
        # Handle user_name
        user_name = data.get("user_name")
        if user_name and isinstance(user_name, str) and len(user_name) > 1:
            memories.append(MemoryEntry(
                category=MemoryCategory.FACT,
                content=f"User's name is {user_name}",
                priority=MemoryPriority.CORE,
                confidence=0.95,
                source_session_id=session_id,
            ))
        
        return memories
    
    def _merge_memories(
        self,
        rule_memories: List[MemoryEntry],
        llm_memories: List[MemoryEntry]
    ) -> List[MemoryEntry]:
        """Merge and deduplicate memories from both sources.
        
        Strategy: Keep rule-based extractions (higher precision),
        add LLM extractions that don't overlap.
        """
        merged = list(rule_memories)
        
        rule_contents_lower = {m.content.lower() for m in rule_memories}
        
        for llm_mem in llm_memories:
            content_lower = llm_mem.content.lower()
            
            # Skip if near-duplicate of rule extraction
            is_duplicate = any(
                self._content_similarity(content_lower, existing) > 0.7
                for existing in rule_contents_lower
            )
            
            if not is_duplicate:
                merged.append(llm_mem)
                rule_contents_lower.add(content_lower)
        
        return merged
    
    @staticmethod
    def _content_similarity(a: str, b: str) -> float:
        """Simple word-overlap similarity (Jaccard)."""
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)
    
    @staticmethod
    def _format_conversation(messages: List[Dict[str, Any]]) -> str:
        """Format messages into readable conversation text."""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")
            if content:
                lines.append(f"{role}: {content}")
        return "\n\n".join(lines)
```

### 2.4 Memory Manager — The Orchestrator

```python
# src/memory/manager.py

"""Memory manager: orchestrates extraction, storage, retrieval, and injection."""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from src.memory.models import (
    MemoryEntry, UserProfile, MemoryCategory, MemoryPriority
)
from src.memory.store import MemoryStore, JSONMemoryStore
from src.memory.extractor import MemoryExtractor
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MemoryManager:
    """Central coordinator for the memory system.
    
    Responsibilities:
    - Load/save user profiles
    - Trigger memory extraction from conversations
    - Build memory-augmented system prompts
    - Handle memory CRUD operations
    - Manage memory lifecycle (decay, consolidation)
    """
    
    # Maximum memories to inject into system prompt
    MAX_INJECTED_MEMORIES = 15
    
    # Maximum characters of memory context to inject
    MAX_MEMORY_CHARS = 1200
    
    # Maximum total memories stored per user (oldest low-priority trimmed)
    MAX_STORED_MEMORIES = 200
    
    def __init__(
        self,
        store: Optional[MemoryStore] = None,
        extractor: Optional[MemoryExtractor] = None,
    ):
        self.store = store or JSONMemoryStore()
        self.extractor = extractor or MemoryExtractor()
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """Load existing profile or create new one."""
        profile = self.store.load_profile(user_id)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self.store.save_profile(profile)
            logger.info(f"Created new profile for {user_id}")
        return profile
    
    def extract_and_save(
        self,
        user_id: str,
        messages: List[Dict[str, Any]],
        session_id: str = ""
    ) -> List[MemoryEntry]:
        """Extract memories from a conversation and save them.
        
        This is the main entry point called when a conversation ends.
        
        Args:
            user_id: User identifier
            messages: Conversation history
            session_id: Current session identifier
            
        Returns:
            List of newly extracted memories
        """
        profile = self.get_or_create_profile(user_id)
        
        if not profile.memory_enabled:
            logger.debug("Memory disabled for user, skipping extraction")
            return []
        
        # Extract new memories
        new_memories = self.extractor.extract_from_conversation(
            messages=messages,
            session_id=session_id,
        )
        
        if not new_memories:
            return []
        
        # Deduplicate against existing memories
        deduplicated = self._deduplicate_against_existing(
            new_memories, profile.active_memories
        )
        
        # Add to profile
        for memory in deduplicated:
            profile.memories.append(memory)
        
        # Trim if over capacity
        self._trim_if_needed(profile)
        
        # Update profile metadata
        profile.last_active_at = datetime.now(timezone.utc).isoformat()
        
        # Extract display name if found
        for mem in deduplicated:
            if mem.category == MemoryCategory.FACT and "name is" in mem.content.lower():
                name = mem.content.split("name is")[-1].strip().rstrip(".")
                if name:
                    profile.display_name = name
        
        # Persist
        self.store.save_profile(profile)
        
        logger.info(
            f"Saved {len(deduplicated)} new memories for {user_id} "
            f"(total: {len(profile.active_memories)})"
        )
        
        return deduplicated
    
    def build_augmented_prompt(
        self,
        user_id: str,
        base_prompt: str,
        current_query: Optional[str] = None
    ) -> str:
        """Build a system prompt augmented with user memories.
        
        Priority injection order:
        1. CORE memories (name, role) — always included
        2. HIGH memories (strong preferences, key facts)
        3. NORMAL memories — if space and relevance allow
        4. Recent conversation summaries (last 3)
        
        Args:
            user_id: User identifier
            base_prompt: Original system prompt
            current_query: Current user message (for relevance scoring)
            
        Returns:
            Augmented system prompt
        """
        profile = self.store.load_profile(user_id)
        
        if profile is None or not profile.memory_enabled:
            return base_prompt
        
        active = profile.active_memories
        if not active:
            return base_prompt
        
        # Sort by priority, then by confidence
        priority_order = {
            MemoryPriority.CORE: 0,
            MemoryPriority.HIGH: 1,
            MemoryPriority.NORMAL: 2,
            MemoryPriority.LOW: 3,
        }
        
        sorted_memories = sorted(
            active,
            key=lambda m: (priority_order.get(m.priority, 9), -m.confidence)
        )
        
        # Build memory sections
        memory_lines = []
        char_count = 0
        memories_used = 0
        summaries_added = 0
        
        for mem in sorted_memories:
            if memories_used >= self.MAX_INJECTED_MEMORIES:
                break
            if char_count + len(mem.content) > self.MAX_MEMORY_CHARS:
                break
            
            # Limit summaries to 3 most recent
            if mem.category == MemoryCategory.SUMMARY:
                if summaries_added >= 3:
                    continue
                summaries_added += 1
            
            # Format line based on category
            line = self._format_memory_line(mem)
            memory_lines.append(line)
            char_count += len(line)
            memories_used += 1
            
            # Mark as accessed
            mem.touch()
        
        if not memory_lines:
            return base_prompt
        
        # Save updated access counts
        self.store.save_profile(profile)
        
        # Build augmented prompt
        greeting = ""
        if profile.display_name:
            greeting = f"The user's name is {profile.display_name}. "
        
        memory_block = "\n".join(memory_lines)
        
        augmented = (
            f"{base_prompt}\n\n"
            f"## What You Know About This User\n"
            f"{greeting}{'' if greeting else ''}\n"
            f"{memory_block}\n\n"
            f"Use this knowledge naturally to provide personalized responses. "
            f"Reference past context when relevant, but don't force it. "
            f"Never say 'according to my memory' — just respond as if you know them."
        )
        
        logger.debug(f"Injected {memories_used} memories ({char_count} chars) into prompt")
        
        return augmented
    
    def _format_memory_line(self, mem: MemoryEntry) -> str:
        """Format a single memory for prompt injection."""
        prefix_map = {
            MemoryCategory.FACT: "•",
            MemoryCategory.PREFERENCE: "• Preference:",
            MemoryCategory.TOPIC: "• Past topic:",
            MemoryCategory.STYLE: "• Communication:",
            MemoryCategory.SUMMARY: "• Previous conversation:",
        }
        prefix = prefix_map.get(mem.category, "•")
        return f"{prefix} {mem.content}"
    
    def _deduplicate_against_existing(
        self,
        new_memories: List[MemoryEntry],
        existing_memories: List[MemoryEntry]
    ) -> List[MemoryEntry]:
        """Remove new memories that duplicate existing ones.
        
        If a new memory contradicts an existing one (same category, similar
        topic but different value), the old one is superseded.
        """
        existing_contents = {m.content.lower() for m in existing_memories}
        
        deduplicated = []
        for new_mem in new_memories:
            content_lower = new_mem.content.lower()
            
            # Exact or near-exact duplicate check
            is_dup = any(
                self._jaccard_similarity(content_lower, existing) > 0.65
                for existing in existing_contents
            )
            
            if is_dup:
                logger.debug(f"Skipping duplicate memory: {new_mem.content[:60]}")
                continue
            
            # Contradiction detection for same-category memories
            for existing_mem in existing_memories:
                if (existing_mem.category == new_mem.category and
                    existing_mem.category in (MemoryCategory.FACT, MemoryCategory.PREFERENCE)):
                    
                    similarity = self._jaccard_similarity(
                        content_lower, existing_mem.content.lower()
                    )
                    # Moderate overlap but not identical = possible update
                    if 0.3 < similarity < 0.65:
                        # Supersede old memory with new one
                        existing_mem.deactivate(superseded_by=new_mem.id)
                        logger.info(
                            f"Memory superseded: '{existing_mem.content[:40]}' → "
                            f"'{new_mem.content[:40]}'"
                        )
            
            deduplicated.append(new_mem)
            existing_contents.add(content_lower)
        
        return deduplicated
    
    @staticmethod
    def _jaccard_similarity(a: str, b: str) -> float:
        """Word-level Jaccard similarity."""
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        return len(words_a & words_b) / len(words_a | words_b)
    
    def _trim_if_needed(self, profile: UserProfile) -> None:
        """Trim memories if over capacity.
        
        Strategy: Remove oldest LOW priority memories first,
        then oldest NORMAL, preserving CORE and HIGH.
        """
        active = [m for m in profile.memories if m.active]
        
        if len(active) <= self.MAX_STORED_MEMORIES:
            return
        
        # Sort by (priority ascending, created_at ascending) — least important + oldest first
        priority_order = {
            MemoryPriority.LOW: 0,
            MemoryPriority.NORMAL: 1,
            MemoryPriority.HIGH: 2,
            MemoryPriority.CORE: 3,
        }
        
        candidates = sorted(
            active,
            key=lambda m: (priority_order.get(m.priority, 0), m.created_at)
        )
        
        # Deactivate excess
        excess = len(active) - self.MAX_STORED_MEMORIES
        for mem in candidates[:excess]:
            mem.deactivate()
        
        logger.info(f"Trimmed {excess} memories for {profile.user_id}")
    
    # --- CRUD Operations for UI ---
    
    def get_all_memories(self, user_id: str) -> List[MemoryEntry]:
        """Get all active memories for UI display."""
        profile = self.store.load_profile(user_id)
        if profile is None:
            return []
        return profile.active_memories
    
    def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        return self.store.remove_memory(user_id, memory_id)
    
    def add_manual_memory(
        self,
        user_id: str,
        content: str,
        category: MemoryCategory = MemoryCategory.FACT
    ) -> MemoryEntry:
        """Manually add a memory (user-initiated)."""
        entry = MemoryEntry(
            category=category,
            content=content,
            priority=MemoryPriority.HIGH,  # Manual = important
            confidence=1.0,                 # User stated it explicitly
            source_session_id="manual",
        )
        self.store.add_memory(user_id, entry)
        logger.info(f"Manual memory added: {content[:60]}")
        return entry
    
    def toggle_memory(self, user_id: str, enabled: bool) -> None:
        """Enable or disable memory for a user."""
        profile = self.get_or_create_profile(user_id)
        profile.memory_enabled = enabled
        self.store.save_profile(profile)
        logger.info(f"Memory {'enabled' if enabled else 'disabled'} for {user_id}")
    
    def forget_everything(self, user_id: str) -> None:
        """Complete memory wipe — right to be forgotten."""
        self.store.clear_all(user_id)
        logger.info(f"Complete memory wipe for {user_id}")
    
    def export_memories(self, user_id: str) -> Dict[str, Any]:
        """Export all memories as a dictionary (for user download)."""
        profile = self.store.load_profile(user_id)
        if profile is None:
            return {"user_id": user_id, "memories": []}
        return profile.to_dict()
```

### 2.5 Integration with ChatService

The existing `ChatService` needs minimal modification. The key touch points:

```python
# src/services/chat_service.py — Modified sections only

from src.memory.manager import MemoryManager


class ChatService(LoggerMixin):
    
    def __init__(
        self,
        client: Optional[NvidiaChatClient] = None,
        state_manager: Optional[ChatStateManager] = None,
        memory_manager: Optional[MemoryManager] = None,  # NEW
    ):
        self.client = client or NvidiaChatClient()
        self.state_manager = state_manager or ChatStateManager()
        self.memory_manager = memory_manager or MemoryManager()
        self.formatter = MessageFormatter()
    
    def stream_message(
        self,
        content: str,
        system_prompt: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        thinking: bool = DEFAULT_THINKING,
        user_id: Optional[str] = None,  # NEW
    ) -> Generator[Tuple[str, str, Optional[Any]], None, None]:
        """Stream message with optional memory augmentation."""
        
        # --- MEMORY INJECTION ---
        if user_id and self.memory_manager:
            system_prompt = self.memory_manager.build_augmented_prompt(
                user_id=user_id,
                base_prompt=system_prompt or "You are a helpful AI assistant.",
                current_query=content,
            )
        
        # Add user message to state
        self.state_manager.add_user_message(content)
        
        # ... rest of existing streaming logic unchanged ...
    
    def clear_conversation(self, user_id: Optional[str] = None) -> None:
        """Clear conversation and extract memories before wiping.
        
        This is the KEY integration point — memories are extracted
        right before the conversation is cleared.
        """
        # --- MEMORY EXTRACTION (before clearing) ---
        if user_id and self.memory_manager and self.state_manager.has_messages:
            try:
                messages = self.state_manager.messages
                session_id = self.state_manager.session_id
                
                new_memories = self.memory_manager.extract_and_save(
                    user_id=user_id,
                    messages=messages,
                    session_id=session_id,
                )
                
                if new_memories:
                    self.logger.info(
                        f"Extracted {len(new_memories)} memories before clearing"
                    )
            except Exception as e:
                self.logger.error(f"Memory extraction failed: {e}")
                # Don't block conversation clearing
        
        self.state_manager.clear_history()
        self.logger.info("Conversation cleared")
```

### 2.6 User Identity — The Bootstrap Problem

Without authentication, we need a lightweight identity mechanism. I propose a three-tier approach:

```python
# src/memory/identity.py

"""Lightweight user identity for memory persistence."""

import uuid
import streamlit as st
from typing import Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


USER_ID_KEY = "memory_user_id"
USER_NAME_KEY = "memory_user_name"
IDENTITY_SET_KEY = "identity_established"


def get_user_id() -> str:
    """Get or create a persistent user ID.
    
    Strategy:
    1. Check session state (current session)
    2. Check query params (bookmark/share link)
    3. Generate new UUID
    
    The ID persists within a browser tab session. For cross-session
    persistence, the user can set a memorable username.
    """
    if USER_ID_KEY in st.session_state:
        return st.session_state[USER_ID_KEY]
    
    # Check for ID in query params (enables cross-device via link)
    params = st.query_params
    if "uid" in params:
        uid = params["uid"]
        st.session_state[USER_ID_KEY] = uid
        return uid
    
    # Generate new
    uid = str(uuid.uuid4())
    st.session_state[USER_ID_KEY] = uid
    return uid


def set_user_identity(username: str) -> str:
    """Set a memorable username as the user ID.
    
    This enables cross-session memory by using a deterministic ID.
    The username is hashed to create a stable user_id.
    
    Args:
        username: User-chosen identifier
        
    Returns:
        Stable user ID derived from username
    """
    import hashlib
    # Create deterministic ID from username
    uid = hashlib.sha256(f"flash-memory-{username.lower().strip()}".encode()).hexdigest()[:20]
    
    st.session_state[USER_ID_KEY] = uid
    st.session_state[USER_NAME_KEY] = username
    st.session_state[IDENTITY_SET_KEY] = True
    
    logger.info(f"User identity set: {username} → {uid[:8]}...")
    return uid


def is_identity_established() -> bool:
    """Check if user has set a memorable identity."""
    return st.session_state.get(IDENTITY_SET_KEY, False)


def render_identity_prompt() -> Optional[str]:
    """Render a non-intrusive identity prompt in the sidebar.
    
    Returns:
        Username if set, None otherwise
    """
    if is_identity_established():
        name = st.session_state.get(USER_NAME_KEY, "")
        return name
    
    return None
```

### 2.7 UI — Memory Panel

This is where the "visible in control" principle materializes. The user can inspect, edit, and manage their memories.

```python
# src/ui/memory_panel.py

"""Memory management UI panel for the sidebar."""

import streamlit as st
from typing import Optional, List

from src.memory.models import MemoryEntry, MemoryCategory, MemoryPriority
from src.memory.manager import MemoryManager
from src.memory.identity import (
    get_user_id,
    set_user_identity,
    is_identity_established,
    render_identity_prompt,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _inject_memory_styles():
    """Inject CSS for memory UI components."""
    st.markdown("""
    <style>
    .memory-entry {
        background: rgba(20, 25, 40, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.5rem;
        font-size: 0.82rem;
        color: #d0d0d0;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 0.5rem;
        transition: border-color 0.2s ease;
    }
    .memory-entry:hover {
        border-color: rgba(0, 255, 224, 0.3);
    }
    .memory-content {
        flex: 1;
        line-height: 1.4;
    }
    .memory-category {
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        font-weight: 600;
        white-space: nowrap;
    }
    .cat-fact { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
    .cat-preference { background: rgba(168, 85, 247, 0.2); color: #c4b5fd; }
    .cat-topic { background: rgba(34, 197, 94, 0.2); color: #86efac; }
    .cat-style { background: rgba(251, 191, 36, 0.2); color: #fde68a; }
    .cat-summary { background: rgba(244, 63, 94, 0.2); color: #fda4af; }
    
    .memory-stats {
        display: flex;
        gap: 1rem;
        padding: 0.6rem 0;
        font-size: 0.78rem;
        color: #9090a0;
    }
    .memory-stats span {
        color: #9090a0 !important;
    }
    .memory-stat-value {
        color: #00ffe0 !important;
        font-weight: 600;
    }
    
    .identity-card {
        background: rgba(0, 255, 224, 0.05);
        border: 1px solid rgba(0, 255, 224, 0.15);
        border-radius: 16px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .identity-greeting {
        font-size: 0.95rem;
        color: #e0e0e0;
    }
    .identity-greeting strong {
        color: #00ffe0;
    }
    </style>
    """, unsafe_allow_html=True)


def render_memory_panel(memory_manager: MemoryManager) -> None:
    """Render the complete memory management panel in the sidebar.
    
    Args:
        memory_manager: Memory manager instance
    """
    _inject_memory_styles()
    
    st.subheader("🧠 Memory")
    
    # --- Identity Section ---
    _render_identity_section(memory_manager)
    
    if not is_identity_established():
        st.caption("Set a username to enable persistent memory across sessions.")
        return
    
    user_id = get_user_id()
    profile = memory_manager.get_or_create_profile(user_id)
    
    # --- Memory Toggle ---
    memory_enabled = st.toggle(
        "Memory active",
        value=profile.memory_enabled,
        key="memory_toggle",
        help="When active, I'll remember key details from our conversations."
    )
    
    if memory_enabled != profile.memory_enabled:
        memory_manager.toggle_memory(user_id, memory_enabled)
        st.rerun()
    
    if not memory_enabled:
        st.caption("Memory is paused. I won't remember this conversation.")
        return
    
    # --- Memory Stats ---
    memories = profile.active_memories
    if memories:
        facts_count = len(profile.facts)
        prefs_count = len(profile.preferences)
        topics_count = len(profile.topics)
        
        st.markdown(
            f'<div class="memory-stats">'
            f'<span><span class="memory-stat-value">{len(memories)}</span> memories</span>'
            f'<span><span class="memory-stat-value">{facts_count}</span> facts</span>'
            f'<span><span class="memory-stat-value">{prefs_count}</span> prefs</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # --- Memory Viewer ---
    if memories:
        with st.expander(f"View memories ({len(memories)})", expanded=False):
            _render_memory_list(memories, memory_manager, user_id)
    else:
        st.caption("No memories yet. Start chatting — I'll learn as we go.")
    
    # --- Memory Actions ---
    _render_memory_actions(memory_manager, user_id, memories)


def _render_identity_section(memory_manager: MemoryManager) -> None:
    """Render identity setup/display."""
    
    if is_identity_established():
        name = st.session_state.get("memory_user_name", "")
        st.markdown(
            f'<div class="identity-card">'
            f'<div class="identity-greeting">Welcome back, <strong>{_escape_html(name)}</strong></div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        with st.form("identity_form", clear_on_submit=True):
            username = st.text_input(
                "Choose a username",
                placeholder="e.g., alex_dev",
                max_chars=30,
                help="This lets me remember you across sessions. Pick something memorable."
            )
            submitted = st.form_submit_button("Remember me", use_container_width=True)
            
            if submitted and username.strip():
                set_user_identity(username.strip())
                st.rerun()


def _render_memory_list(
    memories: List[MemoryEntry],
    memory_manager: MemoryManager,
    user_id: str
) -> None:
    """Render scrollable list of memories with delete buttons."""
    
    category_css = {
        MemoryCategory.FACT: "cat-fact",
        MemoryCategory.PREFERENCE: "cat-preference",
        MemoryCategory.TOPIC: "cat-topic",
        MemoryCategory.STYLE: "cat-style",
        MemoryCategory.SUMMARY: "cat-summary",
    }
    
    for mem in memories:
        col1, col2 = st.columns([0.88, 0.12])
        
        cat_class = category_css.get(mem.category, "cat-fact")
        cat_label = mem.category.value
        
        with col1:
            st.markdown(
                f'<div class="memory-entry">'
                f'<div class="memory-content">{_escape_html(mem.content)}</div>'
                f'<span class="memory-category {cat_class}">{cat_label}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        
        with col2:
            if st.button("🗑", key=f"del_{mem.id}", help="Forget this"):
                memory_manager.delete_memory(user_id, mem.id)
                st.rerun()


def _render_memory_actions(
    memory_manager: MemoryManager,
    user_id: str,
    memories: List[MemoryEntry]
) -> None:
    """Render memory action buttons."""
    
    # Manual memory input
    with st.expander("✏️ Add a memory manually"):
        with st.form("add_memory_form", clear_on_submit=True):
            manual_content = st.text_input(
                "What should I remember?",
                placeholder="e.g., I prefer dark mode in all my apps"
            )
            manual_category = st.selectbox(
                "Category",
                options=[c.value for c in MemoryCategory if c != MemoryCategory.SUMMARY],
                index=0
            )
            add_submitted = st.form_submit_button("Save memory", use_container_width=True)
            
            if add_submitted and manual_content.strip():
                memory_manager.add_manual_memory(
                    user_id=user_id,
                    content=manual_content.strip(),
                    category=MemoryCategory(manual_category),
                )
                st.rerun()
    
    # Danger zone
    if memories:
        st.divider()
        with st.expander("⚠️ Danger zone"):
            if st.button(
                "Forget everything about me",
                type="primary",
                use_container_width=True,
                key="forget_all"
            ):
                memory_manager.forget_everything(user_id)
                st.rerun()
            
            st.caption("This permanently deletes all stored memories.")


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    import html
    return html.escape(text)
```

---

## Phase 3: Memory Lifecycle — The System in Motion

Here is how the memory system behaves across the user journey:

```
FIRST VISIT
    │
    ▼
┌──────────────────────────────────┐
│  No identity set                 │
│  "Choose a username" prompt      │
│  Memory toggle visible but       │
│  inactive until identity set     │
└──────────────┬───────────────────┘
               │ User types "alex_dev"
               ▼
┌──────────────────────────────────┐
│  Identity established            │
│  Empty memory. No augmentation.  │
│  System prompt = base only       │
│  Chat proceeds normally          │
└──────────────┬───────────────────┘
               │ User has conversation
               │ "I'm Alex, a Django dev
               │  working on a fintech API"
               ▼
┌──────────────────────────────────┐
│  User clicks "New Chat" or       │
│  "Clear Conversation"            │
│                                  │
│  TRIGGER: extract_and_save()     │
│  ├─ Rule-based: name → "Alex"    │
│  ├─ LLM-based: role, project     │
│  └─ Dedup & store                │
│                                  │
│  Memories persisted to JSON      │
└──────────────┬───────────────────┘
               │ User returns (next
               │ session or refreshes)
               ▼
┌──────────────────────────────────┐
│  SECOND VISIT                    │
│                                  │
│  User enters "alex_dev" again    │
│  → Deterministic hash → same ID  │
│  → Profile loaded with memories  │
│                                  │
│  System prompt now includes:     │
│  "User's name is Alex"           │
│  "User is a Django developer"    │
│  "Working on a fintech API"      │
│                                  │
│  Bot responds: "Hey Alex,        │
│  how's the fintech API going?"   │
└──────────────────────────────────┘
```

### Memory Decay & Consolidation (Future Enhancement)

```
Every N sessions or on demand:

1. DECAY: Memories not accessed in 30 days → priority downgraded
2. CONSOLIDATE: Similar memories merged
   "User prefers Python" + "User uses Python 3.12" → "User is a Python 3.12 developer"
3. TRIM: Excess memories pruned (oldest low-priority first)
4. CONTRADICTION RESOLUTION: Newer facts supersede older ones
   Old: "User works at StartupA" → Active=false, superseded_by=new_id
   New: "User works at StartupB" → Active=true
```

---

## Phase 4: Risk Analysis & Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| **LLM extraction hallucinates memories** | HIGH | Confidence threshold (0.5+), dual-phase extraction (rules validate LLM), user can delete |
| **Prompt injection via memories** | HIGH | Memories are structured data, never raw user content in system prompt without escaping; extraction prompt constrains output format |
| **Memory injection exceeds context window** | MEDIUM | `MAX_MEMORY_CHARS = 1200` cap, priority-based trimming |
| **User forgets username** | MEDIUM | Display current username in sidebar, allow regeneration. Future: email-based recovery |
| **Multiple users share a username** | LOW | Username is just an identifier for memory grouping. Collision means shared memories — acceptable for non-sensitive use case |
| **HF Spaces filesystem wipe** | HIGH | JSON files are ephemeral. Mitigation: Add export/import buttons so users can backup. Future: use HF Datasets API or external DB |
| **Extraction API cost** | MEDIUM | Only extract on conversation clear (not per-message). Use `temperature=0.1` and `max_tokens=1024` to minimize cost |
| **Memory staleness** | LOW | Supersession logic handles contradictions. Decay system (Phase 2) handles aging |

---

## Phase 5: Integration Touchpoints

The following changes are needed to existing files:

### `src/main.py` — Initialize MemoryManager

```python
from src.memory.manager import MemoryManager
from src.memory.identity import get_user_id

def initialize_app() -> Tuple[ChatService, MemoryManager]:
    # ... existing initialization ...
    
    memory_manager = MemoryManager()
    chat_service = ChatService(memory_manager=memory_manager)
    
    return chat_service, memory_manager

def main() -> None:
    configure_page()
    chat_service, memory_manager = initialize_app()
    
    settings, clear_requested = render_sidebar(memory_manager)
    
    if clear_requested:
        user_id = get_user_id() if is_identity_established() else None
        chat_service.clear_conversation(user_id=user_id)
        st.rerun()
    
    render_chat_interface(chat_service, settings)
```

### `src/ui/sidebar.py` — Add Memory Panel

```python
from src.ui.memory_panel import render_memory_panel

def render_sidebar(memory_manager: MemoryManager) -> Tuple[Dict[str, Any], bool]:
    with st.sidebar:
        # ... existing sliders ...
        
        st.divider()
        render_memory_panel(memory_manager)  # NEW
        
        st.divider()
        # ... existing Document Q&A, Clear button, Model Info ...
```

### `src/ui/chat_interface.py` — Pass user_id to Streaming

```python
from src.memory.identity import get_user_id, is_identity_established

def _handle_user_input(chat_service, prompt, settings):
    # ... existing code ...
    
    user_id = get_user_id() if is_identity_established() else None
    
    stream_generator = chat_service.stream_message(
        content=prompt,
        system_prompt=settings.get("system_prompt"),
        max_tokens=settings.get("max_tokens"),
        temperature=settings.get("temperature"),
        top_p=settings.get("top_p"),
        user_id=user_id,  # NEW — enables memory augmentation
    )
```

---

## Phase 6: New File Structure

```
src/
├── memory/
│   ├── __init__.py           # Public API exports
│   ├── models.py             # MemoryEntry, UserProfile, enums
│   ├── store.py              # MemoryStore (ABC) + JSONMemoryStore
│   ├── extractor.py          # MemoryExtractor (rules + LLM)
│   ├── manager.py            # MemoryManager (orchestrator)
│   ├── identity.py           # User identity (username → stable ID)
│   └── prompts.py            # Extraction/injection prompt templates
├── ui/
│   ├── memory_panel.py       # Memory viewer/editor sidebar component
│   └── ... (existing)
├── services/
│   ├── chat_service.py       # Modified: memory injection + extraction hooks
│   └── ... (existing)
data/
├── memories/                 # JSON memory files (gitignored)
│   └── {user_hash}.json
```

---

## Phase 7: Implementation Checklist

| # | Task | Effort | Priority |
|---|---|---|---|
| 1 | Create `src/memory/models.py` with data classes | 30m | P0 |
| 2 | Create `src/memory/store.py` with JSON backend | 45m | P0 |
| 3 | Create `src/memory/extractor.py` with dual extraction | 1.5h | P0 |
| 4 | Create `src/memory/manager.py` orchestrator | 1h | P0 |
| 5 | Create `src/memory/identity.py` for user ID | 30m | P0 |
| 6 | Create `src/ui/memory_panel.py` | 1h | P0 |
| 7 | Modify `src/services/chat_service.py` — injection + extraction hooks | 45m | P0 |
| 8 | Modify `src/ui/sidebar.py` — add memory panel | 15m | P0 |
| 9 | Modify `src/main.py` — initialization | 15m | P0 |
| 10 | Modify `src/ui/chat_interface.py` — pass user_id | 15m | P0 |
| 11 | Add `data/memories/` to `.gitignore` | 1m | P0 |
| 12 | Write unit tests for extractor and store | 2h | P1 |
| 13 | Add memory export/import UI buttons | 30m | P1 |
| 14 | Implement memory decay (time-based priority reduction) | 1h | P2 |
| 15 | Implement semantic retrieval for episodic memories | 1.5h | P2 |
| 16 | Add memory consolidation (merge similar memories) | 1h | P3 |

**Estimated total for P0:** ~6.5 hours

---

## The "Why" — What Makes This Design Not Generic

Most chatbot memory implementations fall into two traps:

1. **"Dump everything into the system prompt"** — No prioritization, no lifecycle, bloats context.
2. **"Just use a vector database"** — Over-engineered for the scale, loses structured understanding.

This design is different:

- **Structured memory taxonomy** mirrors cognitive science (semantic/episodic/procedural), not a flat key-value store.
- **Dual extraction** (rules + LLM) catches both obvious patterns and subtle implications, with cross-validation.
- **Memory lifecycle** (creation → access tracking → decay → supersession → deletion) prevents staleness.
- **Priority-based injection** respects the context window budget. Core facts always inject; tangential memories only when space allows.
- **Transparency-first UI** — the user sees exactly what's stored. No hidden surveillance. Delete any memory with one click.
- **Storage-agnostic** — `MemoryStore` is abstract. JSON today, Postgres/Redis/HF Datasets tomorrow. Zero changes to the manager or UI.
- **Graceful degradation** — if extraction fails, memory is disabled, or identity isn't set, the chatbot works exactly as before. Memory is additive, never blocking.

The result: the second conversation feels different from the first. The tenth conversation feels like talking to a colleague. The user's investment in the relationship compounds over time, creating genuine retention — not through dark patterns, but through earned familiarity.
