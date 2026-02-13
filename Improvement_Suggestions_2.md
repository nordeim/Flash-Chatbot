

# Meticulous Code Audit: Chatbot with RAG

## Executive Summary

This is a Streamlit-based chatbot integrating NVIDIA's API with a RAG pipeline (sentence-transformers + FAISS). The codebase demonstrates solid modular structure and thoughtful abstraction layers. However, the audit reveals **3 critical bugs**, **6 high-severity issues**, and numerous medium/low concerns spanning security, correctness, architecture, and performance. Below is the full breakdown with remediation.

---

## 🔴 CRITICAL — Breaks Core Functionality

### CRIT-1: Sidebar Layout Collapse — Elements Render in Main Area

**File:** `src/ui/sidebar.py` — Lines 59+

The `with st.sidebar:` context manager exits after the `top_p` slider. Everything below — Document Q&A, Clear Conversation, Model Info — renders in the **main content area**, not the sidebar.

```python
# CURRENT — broken indentation
def render_sidebar() -> Tuple[Dict[str, Any], bool]:
    with st.sidebar:
        st.header(SIDEBAR_TITLE)
        # ... sliders ...
        top_p = st.slider(...)
        
    st.divider()                          # ← MAIN AREA, not sidebar
    st.subheader("📚 Document Q&A")       # ← MAIN AREA
    render_document_upload()              # ← MAIN AREA
    # ...
    clear_requested = st.button(...)      # ← MAIN AREA
    with st.expander("Model Info"):       # ← MAIN AREA
        st.info(...)
```

**Fix:** Move everything inside the `with st.sidebar:` block:

```python
def render_sidebar() -> Tuple[Dict[str, Any], bool]:
    with st.sidebar:
        st.header(SIDEBAR_TITLE)
        
        system_prompt = st.text_area(...)
        st.divider()
        st.subheader("Generation Parameters")
        max_tokens = st.slider(...)
        temperature = st.slider(...)
        top_p = st.slider(...)
        
        st.divider()
        st.subheader("📚 Document Q&A")
        from src.ui.document_upload import render_document_upload
        render_document_upload()
        
        if st.session_state.get("current_document_name"):
            st.caption(f"📄 {st.session_state['current_document_name']}")
            retriever = st.session_state.get("retriever")
            if retriever and hasattr(retriever, 'index') and retriever.index:
                st.caption(f"📊 {retriever.index.ntotal} text chunks in memory")
        
        st.divider()
        clear_requested = st.button(
            "Clear Conversation",
            use_container_width=True,
            type="secondary"
        )
        
        st.divider()
        with st.expander("Model Info"):
            st.info("""...""")
    
    settings = {
        "system_prompt": system_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
    }
    
    return settings, clear_requested
```

---

### CRIT-2: Streaming Response Rendered Outside Chat Message Context

**File:** `src/ui/chat_interface.py` — `_handle_user_input`

The `try:` block that handles streaming is **outside** the `with st.chat_message("assistant")` context. The placeholders created inside the context are updated from outside it, which causes layout corruption — streaming content may render below the chat message container instead of inside it.

```python
# CURRENT — broken scope
with st.chat_message("assistant", avatar="🤖"):
    thinking_placeholder = st.empty()
    content_placeholder = st.empty()
    full_thinking = ""
    full_content = ""

try:                                   # ← OUTSIDE chat_message context
    # ... streaming updates to placeholders happen here
    content_placeholder.markdown(...)  # ← writes to orphaned placeholder
```

**Fix:** Restructure so streaming occurs inside the chat message context:

```python
def _handle_user_input(
    chat_service: ChatService,
    prompt: str,
    settings: Dict[str, Any]
) -> None:
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant", avatar="🤖"):
        thinking_placeholder = st.empty()
        content_placeholder = st.empty()
        
        full_thinking = ""
        full_content = ""
        
        try:
            retriever = st.session_state.get("retriever")
            
            if retriever:
                stream_generator = chat_service.stream_message_with_rag(
                    content=prompt,
                    retriever=retriever,
                    system_prompt=settings.get("system_prompt"),
                    max_tokens=settings.get("max_tokens"),
                    temperature=settings.get("temperature"),
                    top_p=settings.get("top_p"),
                )
            else:
                stream_generator = chat_service.stream_message(
                    content=prompt,
                    system_prompt=settings.get("system_prompt"),
                    max_tokens=settings.get("max_tokens"),
                    temperature=settings.get("temperature"),
                    top_p=settings.get("top_p"),
                )
            
            for thinking, content, reasoning_details in stream_generator:
                if thinking:
                    full_thinking = thinking
                    with thinking_placeholder.container():
                        render_thinking_panel(full_thinking, is_streaming=True)
                if content:
                    full_content = content
                    content_placeholder.markdown(full_content + "▌")
            
            if full_content:
                content_placeholder.markdown(full_content)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            render_error_message(f"Failed to generate response: {str(e)}")
```

---

### CRIT-3: `StreamChunk.reasoning_details` Calls `.get()` on a Pydantic Model

**File:** `src/api/models.py` — `StreamChunk.reasoning_details` property

```python
@property
def reasoning_details(self) -> Optional[Any]:
    if self.choices and self.choices[0].message:
        return self.choices[0].message.get("reasoning_details")  # ← BUG
    return None
```

`self.choices[0].message` is `Optional[Message]` (a Pydantic `BaseModel`), not a `dict`. Calling `.get()` on it raises `AttributeError`. This silently kills reasoning detail extraction during streaming.

**Fix:**

```python
@property
def reasoning_details(self) -> Optional[Any]:
    if self.choices and self.choices[0].message:
        return getattr(self.choices[0].message, "reasoning_details", None)
    return None
```

---

## 🟠 HIGH — Security / Data Integrity

### HIGH-1: XSS via `unsafe_allow_html=True` with Unsanitized Content

**Files:** `src/ui/components.py`, `src/ui/document_upload.py`

Multiple locations inject user-controlled content directly into HTML:

```python
# components.py — render_message_bubble
st.markdown(f"""
    <div class="message-bubble message-user">
        {content}                          # ← raw user input in HTML
    </div>
""", unsafe_allow_html=True)
```

If a user types `<img src=x onerror=alert(1)>`, it executes in the browser. Similarly, filenames in `document_upload.py` are injected without escaping:

```python
f'<span class="filename">{self.state.current_document_name}</span>'
```

A file named `<script>alert('xss')</script>.pdf` would execute.

**Fix:** Sanitize all user content before HTML injection:

```python
import html

def render_message_bubble(content: str, role: str, thinking: Optional[str] = None) -> None:
    escaped_content = html.escape(content)
    st.markdown(f"""
        <div class="message-bubble message-{role}">
            {escaped_content}
        </div>
    """, unsafe_allow_html=True)
```

Better yet, use `st.chat_message` + `st.markdown` (without `unsafe_allow_html`) for user content. Reserve raw HTML only for structural/decorative elements that never contain user data.

---

### HIGH-2: No File Size Limit on Document Upload

**File:** `src/ui/document_upload.py`, `src/rag/document_processor.py`

There is no validation of upload size. A user could upload a 500MB PDF, causing OOM during:
1. `file_bytes = uploaded_file.getvalue()` — loads entire file into memory
2. `processor.process(file_bytes, ...)` — creates chunks in memory
3. `embedder.embed_documents(chunks)` — encodes all chunks
4. FAISS index addition

**Fix:** Add size validation:

```python
# constants.py
MAX_UPLOAD_SIZE_MB = 10
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# document_upload.py — _process_upload
def _process_upload(self, uploaded_file: Any) -> None:
    file_bytes = uploaded_file.getvalue()
    
    if len(file_bytes) > MAX_UPLOAD_SIZE_BYTES:
        placeholder.error(f"❌ File too large. Maximum size: {MAX_UPLOAD_SIZE_MB}MB")
        return
    
    # ... proceed with processing
```

Also add `max_upload_size` to Streamlit's config or `.streamlit/config.toml`.

---

### HIGH-3: No Context Window Management — Unbounded Token Growth

**File:** `src/services/chat_service.py`, `src/services/message_formatter.py`

Every message in conversation history is sent with each API call. With a 128k context window and `DEFAULT_MAX_TOKENS = 65536`, a long conversation will exceed the context window, causing silent truncation or API errors.

**Fix:** Implement a sliding window or token-counting strategy:

```python
# services/message_formatter.py
@staticmethod
def format_messages_for_api(
    history: List[Dict[str, Any]],
    system_prompt: Optional[str] = None,
    max_context_tokens: int = 60000  # Leave room for response
) -> List[Message]:
    messages = []
    
    if system_prompt and system_prompt.strip():
        messages.append(Message(role="system", content=system_prompt.strip()))
    
    # Rough token estimate: 1 token ≈ 4 characters
    # Work backwards from most recent messages
    estimated_tokens = sum(len(m.content) // 4 for m in messages)
    
    eligible = []
    for msg in reversed(history):
        content = msg.get("content", "")
        msg_tokens = len(content) // 4
        if estimated_tokens + msg_tokens > max_context_tokens:
            break
        eligible.insert(0, msg)
        estimated_tokens += msg_tokens
    
    for msg in eligible:
        # ... format as before
    
    return messages
```

---

### HIGH-4: `import_from_json` / `import_conversation` — No Structure Validation

**File:** `src/services/state_manager.py`

```python
def import_conversation(self, data: Dict[str, Any]) -> bool:
    try:
        if "messages" in data:
            self.messages = data["messages"]  # ← accepts ANY structure
            return True
```

This blindly assigns whatever is in `data["messages"]` to session state. An attacker could inject messages with:
- Malicious content (XSS payloads that render when displayed)
- Invalid role values that break rendering logic
- Enormous messages that cause OOM

**Fix:** Validate imported messages:

```python
def import_conversation(self, data: Dict[str, Any]) -> bool:
    try:
        if "messages" not in data:
            return False
        
        validated = []
        for msg in data["messages"]:
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            content = msg.get("content", "")
            if role not in ("user", "assistant", "system"):
                continue
            if not isinstance(content, str) or len(content) > 100_000:
                continue
            validated.append({
                "role": role,
                "content": content,
                "timestamp": msg.get("timestamp", datetime.utcnow().isoformat()),
            })
        
        self.messages = validated
        logger.info(f"Imported {len(validated)} validated messages")
        return True
    except Exception as e:
        logger.error(f"Failed to import conversation: {e}")
        return False
```

---

### HIGH-5: Variable Shadowing in `send_message`

**File:** `src/services/chat_service.py` — `send_message`

```python
def send_message(self, content: str, ...):
    self.state_manager.add_user_message(content)
    # ...
    content = ""  # ← shadows the parameter!
    if response.choices and response.choices[0].message:
        content = response.choices[0].message.content or ""
    
    self.state_manager.add_assistant_message(content)
    return ChatResponse(content=content, finished=True)
```

The parameter `content` (user message) is shadowed by the response content. If the response has no choices, `content` becomes `""` and the assistant message is empty. More dangerously, the variable reuse obscures intent.

**Fix:**

```python
response_content = ""
if response.choices and response.choices[0].message:
    response_content = response.choices[0].message.content or ""

self.state_manager.add_assistant_message(response_content)
return ChatResponse(content=response_content, finished=True)
```

---

### HIGH-6: Broken HTML Wrapping in Document Upload Dropzone

**File:** `src/ui/document_upload.py` — `render` method

```python
st.markdown('<div class="ethereal-dropzone">', unsafe_allow_html=True)
st.markdown('<div class="upload-icon">📄</div>', unsafe_allow_html=True)
st.markdown('<div class="upload-text">Drop your document here</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(...)   # ← Streamlit widget, NOT inside the div

st.markdown('</div>', unsafe_allow_html=True)  # ← Orphaned closing tag
```

Each `st.markdown()` call creates a **separate DOM element**. The `<div class="ethereal-dropzone">` opening tag and `</div>` closing tag are in different elements and **do not wrap** the file uploader. The dropzone styling never applies to the actual upload widget.

**Fix:** Use Streamlit containers instead:

```python
def render(self) -> None:
    _inject_upload_styles()
    
    if self.state.current_document_name:
        self._render_document_badge()
        return
    
    # Use st.container for logical grouping, CSS targets the container
    upload_container = st.container()
    with upload_container:
        uploaded_file = st.file_uploader(
            "📄 Drop your document here (PDF, TXT, MD)",
            type=["pdf", "txt", "md"],
            key="rag_uploader",
            help="Upload a document for context-aware Q&A"
        )
    
    if uploaded_file:
        self._process_upload(uploaded_file)
```

Or use a single `st.markdown` call with all static HTML in one block, and place the uploader separately with CSS targeting `.stFileUploader`.

---

## 🟡 MEDIUM — Correctness / Robustness

### MED-1: `Retriever.__new__` Factory Pattern Is Fragile

**File:** `src/rag/retriever.py`

The `__new__` override to conditionally return `SimpleRetriever` creates several problems:
- `SimpleRetriever(embedder)` calls `Retriever.__new__`, which may return a `Retriever` if FAISS is available — the caller explicitly wanted the simple version but gets the FAISS version.
- The `_is_fallback` attribute is set in `__new__` but never used.
- MRO and `__init__` dispatch becomes confusing.

**Fix:** Use a factory function instead:

```python
def create_retriever(embedder: Embedder) -> "Retriever":
    """Create appropriate retriever based on FAISS availability."""
    try:
        import faiss
        return FAISSRetriever(embedder)
    except ImportError:
        return SimpleRetriever(embedder)
```

Remove `__new__` from `Retriever` entirely. Make `Retriever` an abstract base or protocol.

---

### MED-2: Double Normalization in `SimpleRetriever.retrieve`

**File:** `src/rag/retriever.py`

The embedder is called with `normalize_embeddings=True`, so embeddings are already L2-normalized. Then `retrieve` normalizes again:

```python
query_emb = self.embedder.embed_query(query)
query_emb = query_emb / np.linalg.norm(query_emb)  # ← redundant

embeddings_norm = self._embeddings / np.linalg.norm(self._embeddings, axis=1, keepdims=True)  # ← redundant
```

Not a correctness bug (normalizing a normalized vector is idempotent), but wasted computation on every query.

**Fix:** Remove redundant normalization or make normalization conditional:

```python
def retrieve(self, query: str, k: int = 3) -> List[Tuple[Document, float]]:
    if self._embeddings is None or len(self.documents) == 0:
        return []
    
    query_emb = self.embedder.embed_query(query)
    # Embeddings already normalized by embedder
    similarities = np.dot(self._embeddings, query_emb)
    
    k = min(k, len(self.documents))
    top_indices = np.argsort(similarities)[-k:][::-1]
    
    return [(self.documents[idx], float(similarities[idx])) for idx in top_indices]
```

---

### MED-3: `_chunk_text` Potential Infinite Loop with Misconfigured Overlap

**File:** `src/rag/document_processor.py`

If `chunk_overlap >= chunk_size`, the loop can stall:

```python
start = end - self.chunk_overlap  # could be <= start if overlap >= chunk_size
if start >= end:
    start = end  # This doesn't advance past the current position if end == start
```

**Fix:**

```python
def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
    if chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap ({chunk_overlap}) must be < chunk_size ({chunk_size})")
    self.chunk_size = chunk_size
    self.chunk_overlap = chunk_overlap

def _chunk_text(self, text: str) -> List[str]:
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + self.chunk_size, text_len)
        
        if end < text_len and text[end] not in (" ", "\n", ".", "!", "?"):
            last_space = text.rfind(" ", start, end)
            if last_space > start:  # Only use space if it advances
                end = last_space
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Ensure forward progress
        next_start = end - self.chunk_overlap if end < text_len else text_len
        start = max(next_start, start + 1)  # Always advance at least 1
    
    return chunks
```

---

### MED-4: `NoReturn` Type Hint on `main()` Is Incorrect

**File:** `src/main.py`

```python
def main() -> NoReturn:
```

`NoReturn` means the function **never returns** (e.g., `sys.exit()`). But `main()` can return normally after rendering the Streamlit page. `st.stop()` in `initialize_app` raises `StopException` (caught by Streamlit), not a true non-return.

**Fix:**

```python
def main() -> None:
```

---

### MED-5: `hasattr(st.session_state, 'get')` Is Always True

**File:** `src/ui/chat_interface.py`, `src/ui/sidebar.py`

```python
if hasattr(st.session_state, 'get') and st.session_state.get("retriever"):
```

`st.session_state` is a `SessionState` object that always has `.get()`. This check is vacuous.

**Fix:**

```python
retriever = st.session_state.get("retriever")
if retriever:
    # ...
```

---

### MED-6: Pydantic V1/V2 Compatibility Issues

**Files:** `src/api/models.py`, `src/api/nvidia_client.py`, `src/config/settings.py`

- `@validator` is Pydantic V1 syntax (deprecated in V2, use `@field_validator`)
- `request.dict()` is deprecated in V2 (use `request.model_dump()`)
- `class Config` inside models is V1 pattern (use `model_config` in V2)

If using `pydantic>=2.0` (common with modern `pydantic-settings`), these will emit deprecation warnings or silently break.

**Fix:** Migrate to Pydantic V2 syntax or pin `pydantic<2.0` in requirements.

```python
# V2 syntax example
from pydantic import field_validator

class Message(BaseModel):
    model_config = {"json_schema_extra": {"example": {"role": "user", "content": "Hello"}}}
    
    role: Literal["system", "user", "assistant"]
    content: str = Field(min_length=1)
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        return v.strip()
```

---

### MED-7: Duplicate State Management Patterns

**Files:** `src/ui/document_upload.py`, `src/services/state_manager.py`

`SessionStateWrapper` in `document_upload.py` duplicates state access patterns already in `ChatStateManager`:

```python
# document_upload.py — SessionStateWrapper
class SessionStateWrapper:
    @property
    def retriever(self):
        return st.session_state.get("retriever")

# state_manager.py — ChatStateManager
class ChatStateManager:
    RETRIEVER_KEY = "rag_retriever"      # ← DIFFERENT KEY!
    @property
    def retriever(self):
        return st.session_state.get(self.RETRIEVER_KEY)
```

**Notice:** The keys don't even match! `SessionStateWrapper` uses `"retriever"` while `ChatStateManager` uses `"rag_retriever"`. This means document uploads stored via `SessionStateWrapper` are **invisible** to `ChatStateManager`, and vice versa. The retriever state is fragmented.

**Fix:** Use `ChatStateManager` as the single source of truth. Pass it to `DocumentUpload`:

```python
def render_document_upload(state_manager: ChatStateManager) -> None:
    component = DocumentUpload(state_manager)
    component.render()
```

---

### MED-8: CSS Injected on Every Rerun

**Files:** `src/ui/styles.py`, `src/ui/document_upload.py`, `src/ui/components.py`

`render_custom_css()` and `_inject_upload_styles()` inject CSS on every Streamlit rerun. With frequent user interactions, the DOM accumulates duplicate `<style>` blocks.

**Fix:** Use `st.cache_data` or check before injection:

```python
def render_custom_css() -> None:
    if "css_injected" not in st.session_state:
        st.markdown(get_custom_css(), unsafe_allow_html=True)
        st.session_state["css_injected"] = True
```

Or better, load CSS from a file via `st.markdown` with a stable key, or use Streamlit's theme system.

---

### MED-9: No RAG Relevance Threshold

**File:** `src/services/chat_service.py` — `stream_message_with_rag`

All top-k results are injected regardless of similarity score. Irrelevant chunks dilute context quality:

```python
results = retriever.retrieve(content, k=k)
if results:
    context_chunks = [doc.text for doc, _ in results]  # ← ignores score
```

**Fix:**

```python
RELEVANCE_THRESHOLD = 0.3

results = retriever.retrieve(content, k=k)
relevant = [(doc, score) for doc, score in results if score >= RELEVANCE_THRESHOLD]

if relevant:
    context_chunks = [doc.text for doc, _ in relevant]
    # ...
else:
    logger.info("No sufficiently relevant chunks found, proceeding without context")
```

---

## 🔵 LOW — Code Quality / Maintainability

### LOW-1: `datetime.utcnow()` Deprecated in Python 3.12+

**File:** `src/utils/logger.py`

```python
from datetime import datetime, timezone

# Replace
datetime.utcnow().isoformat()
# With
datetime.now(timezone.utc).isoformat()
```

### LOW-2: Bare `except:` in `nvidia_client.py`

```python
try:
    body = response.json()
except:          # ← catches KeyboardInterrupt, SystemExit
    body = None
```

**Fix:** `except (ValueError, requests.exceptions.JSONDecodeError):`

### LOW-3: `render_chat_container` Has Non-Functional JavaScript

```python
st.markdown("""
    <script>
        const chatContainer = document.querySelector('.main .block-container');
        if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
    </script>
""", unsafe_allow_html=True)
```

Streamlit strips `<script>` tags for security. This code never executes.

### LOW-4: `render_message_bubble` vs `st.chat_message` — Dual Rendering Paths

`components.py` defines `render_message_bubble` with custom HTML, but `chat_interface.py` uses `st.chat_message`. The custom component is never used for the main chat flow, creating dead code.

### LOW-5: `PAGE_ICON = ""` — Empty String

```python
PAGE_ICON = ""  # No icon displayed
```

Should be an actual emoji or icon: `PAGE_ICON = "⚡"`.

### LOW-6: Embedder Error Handling

No error handling if `sentence-transformers` or the model download fails:

```python
@classmethod
def get_model(cls):
    if cls._model is None:
        from sentence_transformers import SentenceTransformer
        cls._model = SentenceTransformer('all-MiniLM-L6-v2')  # ← can fail
    return cls._model
```

**Fix:**

```python
@classmethod
def get_model(cls):
    if cls._model is None:
        try:
            from sentence_transformers import SentenceTransformer
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise RAGError("sentence-transformers not installed. Install with: pip install sentence-transformers")
        except Exception as e:
            raise RAGError(f"Failed to load embedding model: {e}")
    return cls._model
```

### LOW-7: `setup_logging` Clears All Handlers

```python
root_logger.handlers.clear()  # ← kills Streamlit's internal logging
```

This can suppress Streamlit's own log messages and debugging output.

**Fix:** Only add handlers, don't clear existing ones. Or use a named logger instead of root:

```python
app_logger = logging.getLogger("flash_chatbot")
```

---

## Architectural Recommendations

### 1. Unified State Management

The codebase has three state access patterns:
- `ChatStateManager` (uses key `"rag_retriever"`)
- `SessionStateWrapper` in `document_upload.py` (uses key `"retriever"`)
- Direct `st.session_state.get("retriever")` in `chat_interface.py`

**Recommendation:** Make `ChatStateManager` the single state authority. All components should receive it via dependency injection rather than creating their own wrappers.

```
ChatStateManager (single source of truth)
    ├── messages
    ├── retriever
    ├── document_name
    └── pending_prompt

render_sidebar(state_manager) → uses state_manager
render_chat_interface(chat_service) → uses chat_service.state_manager
DocumentUpload(state_manager) → uses state_manager
```

### 2. RAG Pipeline Improvements

```
Current:  Upload → Chunk → Embed → Store → Retrieve → Inject into prompt

Missing:
  ├── Token budget awareness (how much context fits?)
  ├── Chunk metadata (page numbers, source tracking)
  ├── Multi-document support
  ├── Relevance scoring threshold
  └── Chunk deduplication
```

Proposed enhancement for the retriever:

```python
@dataclass
class Document:
    text: str
    metadata: dict = field(default_factory=dict)
    source: str = ""
    page: int = 0
    chunk_index: int = 0

class Retriever(Protocol):
    def add_documents(self, texts: List[str], metadata: Optional[List[dict]] = None) -> None: ...
    def retrieve(self, query: str, k: int = 3, threshold: float = 0.3) -> List[Tuple[Document, float]]: ...
    def clear(self) -> None: ...
    @property
    def document_count(self) -> int: ...
```

### 3. Error Boundary Pattern

Streamlit reruns the entire script on every interaction. Unhandled exceptions crash the page. Implement a decorator:

```python
import functools

def streamlit_error_boundary(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except st.runtime.scriptrunner.StopException:
            raise  # Let st.stop() propagate
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
            st.error(f"Something went wrong: {str(e)}")
            return None
    return wrapper
```

### 4. Test Infrastructure

There are zero tests. Priority test targets:

| Component | Test Type | Priority |
|---|---|---|
| `DocumentProcessor._chunk_text` | Unit | P0 — edge cases with overlap, empty text, single-char |
| `MessageFormatter.format_messages_for_api` | Unit | P0 — history truncation, empty messages |
| `Retriever.retrieve` | Integration | P0 — empty index, single doc, relevance ordering |
| `NvidiaChatClient._make_request` | Unit (mocked) | P1 — error codes, timeout, retry |
| `ChatStateManager` | Unit | P1 — message CRUD, import/export validation |
| `ChatService.stream_message_with_rag` | Integration | P1 — with/without retriever, empty results |

### 5. Dependency Graph Concern

```
main.py
  └── src/main.py
        ├── src/config/* (settings, constants)
        ├── src/api/* (nvidia_client, models, exceptions)
        ├── src/services/* (chat_service, state_manager, message_formatter)
        ├── src/rag/* (document_processor, embedder, retriever)
        ├── src/ui/* (chat_interface, sidebar, document_upload, components, styles)
        └── src/utils/* (logger)
```

The circular-ish import between `sidebar.py → document_upload.py → state_manager.py` and `chat_interface.py → chat_service.py → state_manager.py` should be formalized. Consider an explicit initialization sequence in `main()`:

```python
def main() -> None:
    configure_page()
    state_manager = ChatStateManager()
    chat_service = initialize_app(state_manager)
    settings, clear_requested = render_sidebar(state_manager)
    if clear_requested:
        chat_service.clear_conversation()
        state_manager.clear_retriever()
        st.rerun()
    render_chat_interface(chat_service, settings)
```

---

## Summary Scorecard

| Category | Score | Notes |
|---|---|---|
| **Correctness** | 4/10 | 3 critical bugs, broken layout, orphaned streaming |
| **Security** | 5/10 | XSS vectors, no upload limits, unvalidated imports |
| **Architecture** | 6/10 | Good modular structure, but fragmented state management |
| **Performance** | 6/10 | No context windowing, redundant normalization, CSS duplication |
| **Maintainability** | 7/10 | Clear separation of concerns, good docstrings, but dead code |
| **Testability** | 3/10 | No tests exist, tight Streamlit coupling makes testing hard |
| **RAG Quality** | 5/10 | Functional but lacks threshold, token awareness, metadata |

**Priority remediation order:**
1. Fix CRIT-1 (sidebar layout) — 5 minutes
2. Fix CRIT-2 (streaming scope) — 10 minutes
3. Fix CRIT-3 (`.get()` on model) — 2 minutes
4. Fix HIGH-1 (XSS) — 30 minutes
5. Fix MED-7 (state key mismatch) — 20 minutes
6. Implement HIGH-3 (context window) — 1 hour
7. Add test infrastructure — 2 hours
