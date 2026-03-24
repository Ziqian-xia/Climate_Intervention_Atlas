# OpenAlex Search Behavior Analysis

## Test Results Summary

Tested query: `"climate change health impacts"`

| Search Method | Filter Used | Result Count | Notes |
|---------------|-------------|--------------|-------|
| **Default search** | `search` parameter | **1,273,305** | Searches title + abstract + full-text (when available) |
| **Title only** | `title.search:query` | **2,084** | Title field only |
| **Display name** | `display_name.search:query` | **2,084** | Same as title |
| **Abstract only** | `abstract.search:query` | **101,942** | Abstract field only |
| **Default search filter** | `default.search:query` | **1,273,305** | Same as `search` parameter |

## Key Findings

### 1. OpenAlex `search` Parameter Behavior

According to [OpenAlex documentation](https://docs.openalex.org/how-to-use-the-api/get-lists-of-entities/search-entities):

The `search` parameter searches across:
- ✅ **Title**
- ✅ **Abstract** (inverted index)
- ⚠️ **Full-text** (when available from publisher)

**Problem**: The "full-text when available" part causes inflated results (1.27M vs 2K for title-only)

### 2. Available Filter Options

OpenAlex supports these search filters:
- `title.search:query` - Title only (strict, but may miss relevant papers)
- `abstract.search:query` - Abstract only (misses papers with query in title)
- `default.search:query` - Same as `search` parameter (includes full-text)

### 3. What OpenAlex Does NOT Support

❌ **OR across different fields**: Cannot do `title.search:X|abstract.search:X`
❌ **Exclude full-text**: No way to search title+abstract but exclude full-text
❌ **Custom field combinations**: No direct title-OR-abstract-only search

### 4. Workaround Options

#### Option A: Use `title.search` (Recommended)
```python
filter_str = f"title.search:{query}"
# Results: ~2,000 papers (most precise)
```

**Pros:**
- Most precise - only returns papers with query in title
- Eliminates full-text noise
- Title relevance is usually strong indicator

**Cons:**
- May miss papers where key terms only appear in abstract
- Narrower coverage

#### Option B: Accept `search` parameter (Current)
```python
search_param = "search"
query = user_query
# Results: ~1.27M papers (includes full-text)
```

**Pros:**
- Comprehensive coverage
- Catches all relevant papers

**Cons:**
- Includes full-text matches (less relevant papers)
- Too many results (hard to filter in Phase 3)

#### Option C: Use `abstract.search` only
```python
filter_str = f"abstract.search:{query}"
# Results: ~101K papers (abstract only)
```

**Pros:**
- Focuses on abstract content
- More than title-only

**Cons:**
- Misses papers with query in title but not abstract
- Still quite broad

#### Option D: AND combination (most restrictive)
```python
filter_str = f"title.search:{query},abstract.search:{query}"
# Results: Papers with query in BOTH title AND abstract
```

**Pros:**
- High precision (query must appear in both places)

**Cons:**
- May miss highly relevant papers
- Too restrictive for most use cases

## Recommendation

### For Best Precision: Use Title Search Only

Update `m2_search_exec.py`:

```python
def _execute_openalex(self, max_results: int, out_path: Path) -> Dict:
    """Execute OpenAlex search - Title only for precision."""
    self.logger.agent_thinking("OpenAlex", "Executing title-only search...")

    # Use title.search for most precise results (no full-text inflation)
    filter_str = f"title.search:{self.query}"

    result = self.wrapper.search_works(
        query="",  # Empty when using filter
        search_param="search",
        filter_str=filter_str,  # Title only
        max_results=max_results,
        per_page=100,
        select=""
    )
```

**Expected Results:**
- Query: "climate change health impacts"
- Title-only: ~2,000 papers (vs 1.27M with full search)
- More manageable for Phase 3 screening

## Why Results Vary Between Runs

If you're seeing different result counts (8,000 vs 3,000) with the same query:

1. **Query differences**: Even slight variations in query text cause big changes
   - "climate change health" vs "climate change AND health"
   - Word order matters
   - Stop words, stemming, etc.

2. **OpenAlex database updates**: Database grows daily with new papers

3. **Search parameter differences**:
   - `search` vs `title.search` vs `abstract.search`
   - Different filters applied

4. **Boolean logic in query**:
   - "climate AND health" (narrow)
   - "climate OR health" (broad)
   - "climate health" (phrase search vs AND)

## Testing Other Databases

### PubMed Results Variance (250 → 18)

PubMed uses Entrez query syntax:
```
("climate change"[Title/Abstract] AND "health"[Title/Abstract])
```

Result count depends on:
- Exact phrase matching `"climate change"` vs words `climate change`
- Field tags `[Title/Abstract]` vs `[All Fields]`
- Boolean operators `AND` vs `OR`

To investigate PubMed variance, check:
1. Exact query string sent to API
2. Whether quotes are preserved
3. Field tags are correctly applied

### Scopus

Test shows Scopus is working (62,641 results) but UI reports "Unknown error".

Possible causes:
1. API key not properly passed to wrapper
2. Different query format in UI vs test
3. Timeout or rate limit in UI context
4. Exception swallowed somewhere

## Next Steps

1. **Fix OpenAlex**: Change to `title.search` for precision
2. **Debug Scopus UI error**: Add better error logging
3. **Standardize queries**: Ensure same query is used across runs
4. **Document expected counts**: Set baseline for each query method
