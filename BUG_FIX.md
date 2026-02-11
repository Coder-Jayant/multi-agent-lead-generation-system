# Lead Persistence Bug Fix

## 🐛 Critical Bug Found

**Issue**: Agent scored 9 companies successfully (all with score >= 50), but returned 0 leads to user.

**Root Cause**: `score_company` tool returns scores but **never saves leads to storage**. The agent had no tool to persist leads!

**Evidence from logs**:
```
Scored Iqvia: 75/100 (medium)
Scored Bain: 60/100 (medium)
Scored Vault: 60/100 (medium)
... 9 companies scored ...

✅ Research complete: 0 quality leads collected (out of 0 total)
```

All 9 companies qualified (score >= 50, fit_label = "medium") but were never saved to `leads.json`.

## ✅ Fix Applied

### 1. Created `save_lead` Tool

**File**: `agent/tools/save_lead_tool.py`

New tool that the agent **must call** after `score_company` to persist leads:

```python
@tool
def save_lead(company_data_json, score_data_json, product_description):
    """Save a scored company as a lead to persistent storage."""
    # Creates CompanyLead object
    # Calls add_lead() to persist to leads.json
    # Handles deduplication
    # Returns: {"status": "saved/duplicate/error", "message": "..."}
```

### 2. Updated Controller

**Added to `ALL_TOOLS`**:
```python
ALL_TOOLS = [
    extract_icp,
    generate_search_queries,
    searxng_search,
    normalize_candidates,
    firecrawl_enrich,
    score_company,
    save_lead  # NEW!
]
```

### 3. Updated Controller Prompt

**New Workflow**:
```
firecrawl_enrich(domain) → company_data_json
↓
score_company(company_data_json, icp_json) → score_data_json
↓
save_lead(company_data_json, score_data_json, product_description) → status
↓
Track saved count (duplicates don't count)
```

**Key Prompt Changes**:
- Added `save_lead` to tool list with clear description
- Made it **mandatory**: "MUST call after score_company!"
- Updated workflow to show 3-step process: enrich → score → save
- Changed tracking from "scored count" to "saved count"
- Agent now counts from save_lead responses (ignores duplicates)

## 🧪 Testing

**Restart server**:
```bash
# Stop current server (Ctrl+C)
python start.py
```

**Test with previous input**:
- Same voicebot product description
- Watch logs for `save_lead` calls
- Verify leads appear in `data/leads.json`
- Check UI shows leads at end

**Expected logs**:
```
⚙️ Action: score_company
📊 Observation: {"relevance_score": 75, "fit_label": "medium", ...}
⚙️ Action: save_lead
📊 Observation: {"status": "saved", "message": "Lead saved successfully: Iqvia", ...}
✅ Saved lead: Iqvia (score: 75)
```

## 📊 Impact

**Before**: Scored companies disappeared into void  
**After**: All scored companies persisted to storage

**Without fix**: Agent scores 50 companies → returns 0 leads  
**With fix**: Agent scores 50 companies → saves 50 leads (minus duplicates)

---

**Status**: ✅ Fixed - ready for testing
