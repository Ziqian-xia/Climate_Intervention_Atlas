#!/usr/bin/env python3
"""
Test Scopus search wrapper independently
"""

import sys
import os
from pathlib import Path

# Add scopus-searcher to path
search_packages_base = Path(__file__).parent / "Search and full-text packages" / "search-packages"
scopus_dir = search_packages_base / "scopus-searcher"
sys.path.insert(0, str(scopus_dir))

from scopus_search_wrapper import ScopusSearchWrapper

# Get API credentials from environment
api_key = os.environ.get("SCOPUS_API_KEY", "")
inst_token = os.environ.get("SCOPUS_INST_TOKEN", "")

if not api_key:
    print("❌ Error: SCOPUS_API_KEY environment variable not set")
    print("   Export it: export SCOPUS_API_KEY='your_key'")
    sys.exit(1)

print("=" * 60)
print("Testing Scopus Search Wrapper")
print("=" * 60)

# Create wrapper
print("\n1. Creating wrapper...")
wrapper = ScopusSearchWrapper(
    api_key=api_key,
    inst_token=inst_token,
    timeout=45,
    max_retries=4
)
print("✅ Wrapper created successfully")

# Test query
test_query = 'TITLE-ABS-KEY("climate change" AND "health")'
print(f"\n2. Testing search with query:")
print(f"   {test_query}")

try:
    result = wrapper.search_query(
        query=test_query,
        max_results=10,
        count_per_page=10,
        view="STANDARD"
    )

    print("\n3. Result:")
    print(f"   Success: {result.get('success', False)}")
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Results count: {len(result.get('results', []))}")
    print(f"   Meta count: {result.get('meta_count', 'N/A')}")
    print(f"   API calls: {result.get('calls', 0)}")

    if not result.get('success'):
        print(f"\n❌ Error details:")
        if 'error' in result:
            print(f"   {result['error']}")
        print(f"\n   Full result:")
        import json
        print(json.dumps(result, indent=2))
    else:
        print(f"\n✅ Search successful!")
        if result.get('results'):
            first = result['results'][0]
            print(f"\n   First result sample:")
            print(f"   - Title: {first.get('dc:title', 'N/A')[:100]}...")
            print(f"   - DOI: {first.get('prism:doi', 'N/A')}")

except Exception as e:
    print(f"\n❌ Exception occurred:")
    print(f"   {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
