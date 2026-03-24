#!/usr/bin/env python3
"""
Test SearchExecutor with all three databases
"""

import os
import sys
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.m2_search_exec import SearchExecutor

print("=" * 80)
print("Testing SearchExecutor Module")
print("=" * 80)

# Test configurations
tests = []

# Test 1: OpenAlex
if os.environ.get("OPENALEX_MAILTO"):
    tests.append({
        "name": "OpenAlex",
        "database": "openalex",
        "query": "climate change health impacts",
        "config": {
            "api_key": os.environ.get("OPENALEX_API_KEY", ""),
            "mailto": os.environ.get("OPENALEX_MAILTO", "")
        },
        "max_results": 10
    })
else:
    print("\n⚠️  Skipping OpenAlex: OPENALEX_MAILTO not set")

# Test 2: PubMed
if os.environ.get("PUBMED_EMAIL"):
    tests.append({
        "name": "PubMed",
        "database": "pubmed",
        "query": '("climate change"[Title/Abstract] AND "health"[Title/Abstract])',
        "config": {
            "api_key": os.environ.get("PUBMED_API_KEY", ""),
            "email": os.environ.get("PUBMED_EMAIL", "")
        },
        "max_results": 10
    })
else:
    print("\n⚠️  Skipping PubMed: PUBMED_EMAIL not set")

# Test 3: Scopus
if os.environ.get("SCOPUS_API_KEY"):
    tests.append({
        "name": "Scopus",
        "database": "scopus",
        "query": 'TITLE-ABS-KEY("climate change" AND "health")',
        "config": {
            "api_key": os.environ.get("SCOPUS_API_KEY", ""),
            "inst_token": os.environ.get("SCOPUS_INST_TOKEN", "")
        },
        "max_results": 10
    })
else:
    print("\n⚠️  Skipping Scopus: SCOPUS_API_KEY not set")

if not tests:
    print("\n❌ No database credentials found. Set at least one of:")
    print("   - OPENALEX_MAILTO (required) + OPENALEX_API_KEY (optional)")
    print("   - PUBMED_EMAIL (required) + PUBMED_API_KEY (optional)")
    print("   - SCOPUS_API_KEY (required) + SCOPUS_INST_TOKEN (optional)")
    sys.exit(1)

# Run tests
for test in tests:
    print("\n" + "=" * 80)
    print(f"Testing {test['name']}")
    print("=" * 80)
    print(f"Query: {test['query']}")
    print(f"Max results: {test['max_results']}")

    try:
        executor = SearchExecutor(
            database=test['database'],
            query=test['query'],
            config=test['config']
        )

        out_dir = f"test_output_{test['database']}"
        result = executor.execute_search(
            max_results=test['max_results'],
            out_dir=out_dir
        )

        print(f"\n✅ Search completed!")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Status: {result.get('status', 'unknown')}")
        print(f"   Results count: {result.get('results_count', 0)}")

        if result.get('output_files'):
            print(f"   Output files:")
            for key, path in result['output_files'].items():
                exists = Path(path).exists()
                size = Path(path).stat().st_size if exists else 0
                print(f"      - {key}: {path} ({'✓' if exists else '✗'}, {size} bytes)")

        if not result.get('success'):
            print(f"\n⚠️  Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"\n❌ Exception occurred:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("All tests completed")
print("=" * 80)
