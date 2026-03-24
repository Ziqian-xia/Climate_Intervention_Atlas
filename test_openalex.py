#!/usr/bin/env python3
"""
Test OpenAlex search wrapper independently
"""

import sys
import os
from pathlib import Path

# Add openalex-searcher to path
search_packages_base = Path(__file__).parent / "Search and full-text packages" / "search-packages"
openalex_dir = search_packages_base / "openalex-searcher"
sys.path.insert(0, str(openalex_dir))

from openalex_search_wrapper import OpenAlexSearchWrapper

# Get API credentials from environment
api_key = os.environ.get("OPENALEX_API_KEY", "")
mailto = os.environ.get("OPENALEX_MAILTO", "")

print("=" * 60)
print("Testing OpenAlex Search Wrapper")
print("=" * 60)

if not mailto:
    print("⚠️  Warning: OPENALEX_MAILTO not set (recommended for politeness)")
    print("   Export it: export OPENALEX_MAILTO='your@email.com'")

if not api_key:
    print("⚠️  Info: No API key (rate limits may apply)")
else:
    print("✅ API key provided")

# Create wrapper
print("\n1. Creating wrapper...")
wrapper = OpenAlexSearchWrapper(
    api_key=api_key,
    mailto=mailto,
    timeout=45,
    max_retries=4
)
print("✅ Wrapper created successfully")

# Test 1: Full-text search (old method)
print("\n" + "=" * 60)
print("TEST 1: Full-text search (old method)")
print("=" * 60)
test_query_fulltext = "climate change health impacts"
print(f"Query: {test_query_fulltext}")

try:
    result = wrapper.search_works(
        query=test_query_fulltext,
        search_param="search",  # Full-text search
        max_results=10,
        per_page=10,
        select=""
    )

    print(f"\nResult:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Results count: {len(result.get('results', []))}")
    print(f"   Meta count: {result.get('meta_count', 'N/A')}")
    print(f"   API calls: {result.get('calls', 0)}")

    if result.get('success') and result.get('results'):
        first = result['results'][0]
        print(f"\n   First result:")
        print(f"   - Title: {first.get('title', 'N/A')[:100]}...")
        print(f"   - DOI: {first.get('doi', 'N/A')}")

except Exception as e:
    print(f"\n❌ Exception: {type(e).__name__}: {str(e)}")

# Test 2: Title+Abstract search (new method)
print("\n" + "=" * 60)
print("TEST 2: Title+Abstract search (new method)")
print("=" * 60)
test_query_ta = "climate change health impacts"
filter_str = f"title.search:{test_query_ta}|abstract.search:{test_query_ta}"
print(f"Query: {test_query_ta}")
print(f"Filter: {filter_str}")

try:
    result = wrapper.search_works(
        query="",  # Empty when using filter
        search_param="search",
        filter_str=filter_str,  # Title OR Abstract
        max_results=10,
        per_page=10,
        select=""
    )

    print(f"\nResult:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Results count: {len(result.get('results', []))}")
    print(f"   Meta count: {result.get('meta_count', 'N/A')}")
    print(f"   API calls: {result.get('calls', 0)}")

    if not result.get('success'):
        print(f"\n❌ Error details:")
        if 'error' in result:
            print(f"   {result['error']}")
    else:
        print(f"\n✅ Title+Abstract search successful!")
        if result.get('results'):
            first = result['results'][0]
            print(f"\n   First result:")
            print(f"   - Title: {first.get('title', 'N/A')[:100]}...")
            print(f"   - DOI: {first.get('doi', 'N/A')}")
            # Check if abstract exists
            abstract_idx = first.get('abstract_inverted_index')
            print(f"   - Has abstract: {bool(abstract_idx)}")

except Exception as e:
    print(f"\n❌ Exception: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
