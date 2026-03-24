#!/usr/bin/env python3
"""
Simulate UI's Scopus search execution to debug "Unknown error"
"""

import sys
import os
from pathlib import Path

# Add modules to path (same as app.py)
sys.path.insert(0, str(Path(__file__).parent))

from modules.m2_search_exec import SearchExecutor
from utils.logger import get_logger

logger = get_logger()

print("=" * 80)
print("Scopus UI Simulation Test")
print("=" * 80)

# Use same credentials as .env.test
scopus_key = os.environ.get("SCOPUS_API_KEY", "f0f4a2ca58b215d8f580b48f5083dc0c")
scopus_insttoken = os.environ.get("SCOPUS_INST_TOKEN", "")

# Test query (from UI)
query = 'TITLE-ABS-KEY("climate change" AND "health")'
max_results = 100
out_dir = "test_scopus_ui_output"

print(f"\nConfiguration:")
print(f"  API Key: {scopus_key[:10]}...{scopus_key[-4:]}")
print(f"  Inst Token: {'(set)' if scopus_insttoken else '(not set)'}")
print(f"  Query: {query}")
print(f"  Max results: {max_results}")
print(f"  Output dir: {out_dir}")

# Simulate UI's config dictionary construction
config = {
    "api_key": scopus_key,
    "mailto": "",
    "email": "",
    "inst_token": scopus_insttoken
}

print(f"\nConfig dict:")
for k, v in config.items():
    if v:
        print(f"  {k}: {v[:20] if len(str(v)) > 20 else v}...")
    else:
        print(f"  {k}: (empty)")

print("\n" + "=" * 80)
print("Executing search...")
print("=" * 80)

try:
    # This is exactly how UI calls it
    executor = SearchExecutor("scopus", query, config)
    result = executor.execute_search(max_results=max_results, out_dir=out_dir)

    print(f"\n✅ Search execution completed")
    print(f"\nResult dictionary:")
    for key, value in result.items():
        if key == "output_files":
            print(f"  {key}:")
            for fkey, fpath in value.items():
                exists = Path(fpath).exists()
                print(f"    - {fkey}: {fpath} ({'✓' if exists else '✗'})")
        else:
            print(f"  {key}: {value}")

    # Check success status
    if result["success"]:
        print(f"\n✅ SUCCESS: Found {result['results_count']} results")

        # Verify output files
        csv_path = result["output_files"]["summary_csv"]
        if Path(csv_path).exists():
            import pandas as pd
            df = pd.read_csv(csv_path)
            print(f"\nCSV preview (first 3 rows):")
            print(df.head(3).to_string())
        else:
            print(f"\n⚠️  Warning: CSV file not found at {csv_path}")
    else:
        print(f"\n❌ FAILED:")
        print(f"  Status: {result.get('status', 'unknown')}")
        print(f"  Error: {result.get('error', 'Unknown error')}")

except Exception as e:
    print(f"\n❌ Exception caught:")
    print(f"  Type: {type(e).__name__}")
    print(f"  Message: {str(e)}")

    import traceback
    print(f"\n  Full traceback:")
    traceback.print_exc()

    # This is what UI does on exception
    result = {
        "success": False,
        "status": "error",
        "error": str(e),
        "results_count": 0,
        "output_files": {}
    }
    print(f"\n  Result dict that UI would create:")
    print(f"    {result}")

print("\n" + "=" * 80)
