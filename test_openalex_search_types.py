#!/usr/bin/env python3
"""
Test OpenAlex different search types to understand behavior
"""

import sys
import os
from pathlib import Path

# Add openalex-searcher to path
search_packages_base = Path(__file__).parent / "Search and full-text packages" / "search-packages"
openalex_dir = search_packages_base / "openalex-searcher"
sys.path.insert(0, str(openalex_dir))

from openalex_search_wrapper import OpenAlexSearchWrapper

# Get API credentials
api_key = os.environ.get("OPENALEX_API_KEY", "")
mailto = os.environ.get("OPENALEX_MAILTO", "")

print("=" * 80)
print("OpenAlex Search Types Comparison")
print("=" * 80)

wrapper = OpenAlexSearchWrapper(
    api_key=api_key,
    mailto=mailto,
    timeout=45,
    max_retries=4
)

test_query = "climate change health impacts"

tests = [
    {
        "name": "1. Default 'search' parameter (current method)",
        "params": {
            "query": test_query,
            "search_param": "search",
            "filter_str": "",
            "max_results": 5
        }
    },
    {
        "name": "2. title.search filter only",
        "params": {
            "query": "",
            "search_param": "search",
            "filter_str": f"title.search:{test_query}",
            "max_results": 5
        }
    },
    {
        "name": "3. display_name.search (abstract NOT included)",
        "params": {
            "query": "",
            "search_param": "search",
            "filter_str": f"display_name.search:{test_query}",
            "max_results": 5
        }
    },
    {
        "name": "4. Raw abstract text filter",
        "params": {
            "query": "",
            "search_param": "search",
            "filter_str": f"raw_abstract.search:{test_query}",
            "max_results": 5
        }
    },
    {
        "name": "5. Combined title OR abstract (if supported)",
        "params": {
            "query": "",
            "search_param": "search",
            "filter_str": f"default.search:{test_query}",  # Try default.search
            "max_results": 5
        }
    }
]

for test in tests:
    print("\n" + "=" * 80)
    print(test["name"])
    print("=" * 80)
    print(f"Query: '{test_query}'")
    print(f"Params: {test['params']}")

    try:
        result = wrapper.search_works(**test["params"])

        print(f"\nResult:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Results: {len(result.get('results', []))}")
        print(f"  Meta count: {result.get('meta_count', 'N/A')}")

        if not result.get('success'):
            print(f"\n  ❌ Error: {result.get('error', 'Unknown')}")
        else:
            if result.get('meta_count'):
                print(f"  ✅ Total matches in database: {result['meta_count']:,}")

            if result.get('results'):
                first = result['results'][0]
                print(f"\n  Sample result:")
                print(f"    Title: {first.get('title', 'N/A')[:80]}...")

                # Check if abstract exists
                abstract_idx = first.get('abstract_inverted_index')
                has_abstract = bool(abstract_idx)
                print(f"    Has abstract: {has_abstract}")
                if has_abstract:
                    # Reconstruct first 100 chars
                    from openalex_search_wrapper import reconstruct_abstract
                    abstract = reconstruct_abstract(abstract_idx)
                    print(f"    Abstract preview: {abstract[:100]}...")

    except Exception as e:
        print(f"\n  ❌ Exception: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("""
Based on OpenAlex documentation (https://docs.openalex.org/):

- `search` parameter: Searches across title, abstract inverted index, and full-text when available
- `title.search`: Only searches title field
- `display_name.search`: Title field (alternative name)
- `raw_abstract.search`: May exist but not documented well
- `default.search`: Searches title + abstract (closest to what we want)

For Title+Abstract only search, we need to use 'default.search' filter.
""")
