#!/usr/bin/env python3
"""
Test PubMed search wrapper independently
"""

import sys
import os
from pathlib import Path

# Add pubmed-searcher to path
search_packages_base = Path(__file__).parent / "Search and full-text packages" / "search-packages"
pubmed_dir = search_packages_base / "pubmed-searcher"
sys.path.insert(0, str(pubmed_dir))

from pubmed_search_wrapper import PubMedSearchWrapper, parse_pubmed_xml

# Get API credentials from environment
api_key = os.environ.get("PUBMED_API_KEY", "")
email = os.environ.get("PUBMED_EMAIL", "")

print("=" * 60)
print("Testing PubMed Search Wrapper")
print("=" * 60)

if not email:
    print("⚠️  Warning: PUBMED_EMAIL not set (recommended)")
    print("   Export it: export PUBMED_EMAIL='your@email.com'")

if not api_key:
    print("⚠️  Warning: PUBMED_API_KEY not set (rate limit: 3 req/s)")
    print("   Export it: export PUBMED_API_KEY='your_ncbi_key'")
else:
    print("✅ API key provided (rate limit: 10 req/s)")

# Create wrapper
print("\n1. Creating wrapper...")
wrapper = PubMedSearchWrapper(
    api_key=api_key,
    email=email,
    timeout=45,
    max_retries=4
)
print("✅ Wrapper created successfully")

# Test query
test_query = '("climate change"[Title/Abstract] AND "health"[Title/Abstract])'
print(f"\n2. Testing ESearch with query:")
print(f"   {test_query}")

try:
    # Step 1: ESearch
    esearch_result = wrapper.esearch(
        query=test_query,
        max_results=10
    )

    print("\n3. ESearch result:")
    print(f"   OK: {esearch_result.get('ok', False)}")
    print(f"   Total count: {esearch_result.get('count_total', 0)}")
    print(f"   Target count: {esearch_result.get('count_target', 0)}")

    if not esearch_result.get('ok'):
        print(f"\n❌ ESearch failed:")
        print(f"   Status: {esearch_result.get('status')}")
        import json
        print(json.dumps(esearch_result, indent=2))
    else:
        query_key = esearch_result['query_key']
        webenv = esearch_result['webenv']
        target_count = esearch_result['count_target']

        print(f"   Query key: {query_key}")
        print(f"   WebEnv: {webenv[:20]}...")

        # Step 2: EFetch
        print(f"\n4. Testing EFetch (retrieving {min(5, target_count)} records)...")
        efetch_result = wrapper.efetch_batch(
            query_key=query_key,
            webenv=webenv,
            retstart=0,
            retmax=min(5, target_count)
        )

        print(f"   OK: {efetch_result.get('ok', False)}")

        if not efetch_result.get('ok'):
            print(f"\n❌ EFetch failed:")
            print(f"   Status: {efetch_result.get('status')}")
        else:
            # Step 3: Parse XML
            print(f"\n5. Parsing XML...")
            records = parse_pubmed_xml(efetch_result['xml'])
            print(f"   Parsed {len(records)} records")

            if records:
                first = records[0]
                print(f"\n   First record sample:")
                print(f"   - PMID: {first.get('pmid', 'N/A')}")
                print(f"   - Title: {first.get('title', 'N/A')[:100]}...")
                print(f"   - Abstract: {first.get('abstract', 'N/A')[:100]}...")
                print(f"   - DOI: {first.get('doi', 'N/A')}")

            print(f"\n✅ PubMed test successful!")

except Exception as e:
    print(f"\n❌ Exception occurred:")
    print(f"   {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
