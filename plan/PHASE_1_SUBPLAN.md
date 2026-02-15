# Phase 1 Sub-Plan: Critical Bug Fixes

## Overview
**Phase:** 1 - Critical Bug Fixes (IMMEDIATE)
**Issue:** CRIT-3 - Pydantic `.get()` bug breaks reasoning_details extraction
**Estimated Time:** 15 minutes
**Risk Level:** Low
**Status:** ✅ COMPLETED

---

## Execution Summary

### Date: 2026-02-15
### Result: SUCCESS ✅

### What Was Fixed
**File:** `src/api/models.py` - Line 116
**Issue:** `StreamChunk.reasoning_details` property called `.get()` on a Pydantic model instead of using `getattr()`

**Before:**
```python
return self.choices[0].message.get("reasoning_details")  # AttributeError!
```

**After:**
```python
return getattr(self.choices[0].message, "reasoning_details", None)
```

### Test-Driven Development Steps

1. **✅ RED (Write failing test):** Added 4 comprehensive tests for `reasoning_details` property
   - `test_reasoning_details_extraction` - Tests successful extraction
   - `test_reasoning_details_none` - Tests when reasoning_details not present
   - `test_reasoning_details_empty_choices` - Tests empty choices list
   - `test_reasoning_details_none_message` - Tests when message is None

2. **✅ GREEN (Make test pass):** Applied the fix by replacing `.get()` with `getattr()`

3. **✅ REFACTOR (Verify no regressions):** All 25 existing tests still pass

### Test Results
```
tests/unit/test_api_models.py::TestStreamChunk::test_reasoning_details_extraction PASSED
tests/unit/test_api_models.py::TestStreamChunk::test_reasoning_details_none PASSED
tests/unit/test_api_models.py::TestStreamChunk::test_reasoning_details_empty_choices PASSED
tests/unit/test_api_models.py::TestStreamChunk::test_reasoning_details_none_message PASSED

25 passed in 0.39s
```

### Files Modified
1. `src/api/models.py` - Fixed `.get()` → `getattr()` on line 116
2. `tests/unit/test_api_models.py` - Added 4 new test cases

### Verification Checklist
- [x] Write failing test demonstrating the bug
- [x] Apply code fix
- [x] Verify test passes
- [x] Run full test suite - all 25 tests pass
- [x] No regressions introduced
- [x] Code follows project conventions

### Impact
- **Before:** `reasoning_details` property raised `AttributeError` during streaming, causing silent failure
- **After:** `reasoning_details` correctly extracted using `getattr()`, enabling thinking/reasoning display during streaming

### Risk Assessment
- **Risk Level:** Low
- **Breaking Changes:** None
- **Rollback:** Simple - just revert line 116 to use `.get()`

---

## Next Steps

Proceed to **Phase 2: Security Hardening** 

Issues to address:
- HIGH-1: XSS vulnerabilities in components.py and document_upload.py
- HIGH-2: No file size limit on uploads
- HIGH-4: Import validation missing in state_manager.py
- HIGH-5: Variable shadowing in chat_service.py

---

## Notes

The LSP error that originally flagged this issue is now resolved:
```
ERROR [145:44] Cannot access attribute "get" for class "Message" Attribute "get" is unknown
```

*Phase 1 Complete - Ready for Phase 2*
