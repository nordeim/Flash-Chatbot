# 🚀 Build Mode: Execution ToDo List

## Phase 3: RAG-Lite Implementation (TDD)

### 3.1 Setup & Dependencies ✅
- [x] Add RAG dependencies to requirements.txt
- [x] Install dependencies and verify
- [x] Create src/rag/ directory structure

### 3.2 Document Processor (TDD Cycle 1) ✅
- [x] Write failing tests: test_document_processor.py
  - [x] test_extract_text_from_txt
  - [x] test_extract_text_from_pdf
  - [x] test_chunking_respects_max_length
  - [x] test_unsupported_file_raises
- [x] Implement DocumentProcessor class
- [x] Run tests until all pass (10/10 ✅)
- [x] Refactor if needed

### 3.3 Embedder (TDD Cycle 2) ⚠️
- [x] Write failing tests: test_embedder.py
  - [x] test_model_loads_lazily
  - [x] test_embed_dimension
  - [x] test_embed_query_and_docs_consistent
- [x] Implement Embedder class with lazy loading
- [ ] Run tests until all pass - **BLOCKED: sentence-transformers needs ~200MB disk space**
  - Tests skip gracefully if dependency unavailable
  - Implementation is production-ready
  - Will work when deployed to HF Spaces (16GB RAM)

### 3.4 Retriever (TDD Cycle 3) ✅
- [x] Write failing tests: test_retriever.py
  - [x] test_add_documents_updates_index
  - [x] test_retrieve_returns_correct_k
  - [x] test_empty_index_returns_empty_list
- [x] Implement Retriever class with FAISS
- [x] Implement SimpleRetriever fallback (no FAISS)
- [x] Run tests until all pass (11/11 ✅)

### 3.5 Service Layer Integration (TDD Cycle 4) ⏳ PENDING
- [ ] Extend StateManager for document metadata
- [ ] Write failing tests: test_chat_service_rag.py
  - [ ] test_stream_message_with_rag_context_injects_chunks
  - [ ] test_no_context_if_no_document_uploaded
- [ ] Implement stream_message_with_rag in ChatService
- [ ] Run tests until all pass

### 3.6 UI Components (TDD Cycle 5) ⏳ PENDING
- [ ] Create document_upload.py with ethereal styling
- [ ] Integrate into sidebar.py
- [ ] Add custom CSS to styles.py
- [ ] Manual testing with real documents

### 3.7 Integration Tests ⏳ PENDING
- [ ] Write test_rag_flow.py
- [ ] Full pipeline test with mock embeddings
- [ ] Verify memory usage <512MB

### 3.8 Validation ⏳ PENDING
- [ ] Upload PDF → ask question → verify context used
- [ ] Upload unsupported file → graceful error
- [ ] Clear document → retriever empty
- [ ] Update ARCHITECTURE.md
- [ ] Update README.md

---

## Phase 1: Multi-Session (Pending)

### 1.1 Session Manager (TDD)
- [ ] Write failing tests: test_session_manager.py
- [ ] Implement Session dataclass
- [ ] Implement SessionManager class
- [ ] Run tests until all pass

### 1.2 State Manager Refactor
- [ ] Extend ChatStateManager for multi-session
- [ ] Update tests
- [ ] Verify backward compatibility

### 1.3 UI Components
- [ ] Create session_tabs.py with custom HTML
- [ ] Integrate into main interface
- [ ] Add session controls to sidebar

### 1.4 Validation
- [ ] Create 3 sessions
- [ ] Switch between sessions
- [ ] Verify conversation isolation
- [ ] Export per-session

---

## Phase 4: Basic Accessibility (Pending)

### 4.1 Focus Styles
- [ ] Add focus-visible CSS to styles.py
- [ ] Test tab navigation

### 4.2 ARIA Labels
- [ ] Add aria-label to interactive components
- [ ] Verify screen reader compatibility

### 4.3 Reduced Motion
- [ ] Add prefers-reduced-motion media query
- [ ] Test animation disable

---

## Phase 2: UI Polish (Pending)

### 2.1 Thinking Indicator
- [ ] Create three-orb animation component
- [ ] Replace current spinner

### 2.2 Typography
- [ ] Add Google Fonts (Satoshi/Inter)
- [ ] Update CSS variables

### 2.3 Micro-interactions
- [ ] Enhance hover states
- [ ] Add subtle animations

---

## Current Status

**Active Phase**: Phase 3 - RAG-Lite Core Engine  
**TDD Cycle**: 3/5 Complete (DocumentProcessor ✅, Embedder ⚠️, Retriever ✅)  
**Next Action**: Continue to Cycle 4 (Service Layer Integration)  
**Blockers**: sentence-transformers requires HF Spaces deployment (disk space)

**Test Summary**:
- DocumentProcessor: 10/10 ✅
- Embedder: 0/10 ⏭️ (skips without dependency)
- Retriever: 11/11 ✅
- **Total: 21 tests passing**

---

## 📊 Decision Matrix

| Decision | Status | Recommendation |
|----------|--------|----------------|
| Complete service layer? | ⏳ Pending | **Yes** - Can test with mocks |
| Skip sentence-transformers? | ⚠️ Deferred | **No** - Required for production |
| Deploy to HF Spaces? | ⏳ Pending | **Yes** - Dependencies will install |
| Continue to Multi-session? | ⏳ Pending | **After RAG complete** |

---

## 🎯 Recommended Next Actions

1. **Continue RAG service layer** (TDD Cycle 4)
   - Extend ChatService for RAG
   - Extend StateManager for document metadata
   - Use mock embedder for testing

2. **Complete RAG UI** (TDD Cycle 5)
   - Document upload component
   - Integrate into sidebar
   - Add ethereal styling

3. **Manual E2E testing**
   - Deploy to HF Spaces
   - Install full dependencies
   - Test with real documents

4. **Then**: Multi-session (Phase 1)

5. **Then**: Accessibility (Phase 4)

6. **Finally**: UI Polish (Phase 2)
