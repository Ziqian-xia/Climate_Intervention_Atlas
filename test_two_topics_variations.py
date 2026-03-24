#!/usr/bin/env python3
"""
测试两个研究主题的5-variation结果
Topic 1: Cool and green roofs
Topic 2: Weather forecasts
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from modules.m1_query_gen import QueryGenerationTeam
from modules.m2_search_exec import SearchExecutor
from utils.llm_providers import create_llm_provider
from utils.logger import get_logger

logger = get_logger()

# 两个研究主题
TOPICS = {
    "topic1_green_roofs": """I am interested in research papers on the impacts of cool and green roofs interventions on the temperature–health relationship. I am specifically interested in papers with causal research designs—i.e., papers that can isolate the impact of plausibly random assignment (experimental or quasi-experimental) of cooling centers to a population of interest. Papers from anywhere in the world on any population would be of interest.""",

    "topic2_weather_forecast": """I am interested in research papers on the impacts of weather forecasts interventions on the temperature–health relationship. I am specifically interested in papers with causal research designs—i.e., papers that can isolate the impact of plausibly random assignment (experimental or quasi-experimental) of cooling centers to a population of interest. Papers from anywhere in the world on any population would be of interest."""
}

def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

def generate_variations(provider, topic_key: str, topic: str, num_variations: int = 5) -> List[Dict]:
    """为一个主题生成多个查询变体"""
    print_section(f"{topic_key.upper()}: Generating {num_variations} Query Variations")

    team = QueryGenerationTeam(llm_provider=provider)
    all_variations = []

    for var_idx in range(1, num_variations + 1):
        print(f"\n{'='*80}")
        print(f"Generating Variation #{var_idx}")
        print(f"{'='*80}")

        result = team.generate_queries(topic, variation_seed=var_idx)

        # Extract queries from refiner output
        refiner_queries = result.get('refiner_queries', {})

        if refiner_queries and refiner_queries.get('openalex_query'):
            variation_data = {
                "variation_seed": var_idx,
                "pulse_keywords": result.get('pulse_keywords', []),
                "queries": {
                    "elsevier_query": refiner_queries.get('elsevier_query', ''),
                    "pubmed_query": refiner_queries.get('pubmed_query', ''),
                    "openalex_query": refiner_queries.get('openalex_query', '')
                }
            }
            all_variations.append(variation_data)

            print(f"✅ Variation #{var_idx} generated successfully")
            print(f"   Keywords: {len(variation_data['pulse_keywords'])}")
            print(f"   OpenAlex query length: {len(variation_data['queries']['openalex_query'])} chars")
        else:
            print(f"❌ Variation #{var_idx} failed")

    return all_variations

def search_single_variation(db: str, variation: Dict, max_results: int, out_dir: str) -> Dict:
    """搜索单个variation"""
    var_idx = variation['variation_seed']

    configs = {
        "openalex": {
            "api_key": os.environ.get("OPENALEX_API_KEY", ""),
            "mailto": os.environ.get("OPENALEX_MAILTO", "")
        },
        "pubmed": {
            "api_key": os.environ.get("PUBMED_API_KEY", ""),
            "email": os.environ.get("PUBMED_EMAIL", "")
        },
        "scopus": {
            "api_key": os.environ.get("SCOPUS_API_KEY", ""),
            "inst_token": os.environ.get("SCOPUS_INST_TOKEN", "")
        }
    }

    query_map = {
        "openalex": variation['queries']['openalex_query'],
        "pubmed": variation['queries']['pubmed_query'],
        "scopus": variation['queries']['elsevier_query']
    }

    query = query_map[db]
    config = configs[db]

    try:
        executor = SearchExecutor(db, query, config)
        var_out_dir = f"{out_dir}/variation_{var_idx}"
        result = executor.execute_search(max_results=max_results, out_dir=var_out_dir)

        # Read meta_count from summary
        summary_file = Path(var_out_dir) / "run_summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
                meta_count = summary.get("meta_count", 0)
        else:
            meta_count = result.get("results_count", 0)

        return {
            "success": result.get("success", False),
            "variation_idx": var_idx,
            "meta_count": meta_count,
            "retrieved": result.get("results_count", 0),
            "out_dir": var_out_dir,
            "output_files": result.get("output_files", {})
        }
    except Exception as e:
        logger.error(f"Search failed for {db} variation {var_idx}: {e}")
        return {
            "success": False,
            "variation_idx": var_idx,
            "meta_count": 0,
            "retrieved": 0,
            "error": str(e)
        }

def merge_variations(db: str, variation_results: List[Dict], base_out_dir: str) -> Dict:
    """合并多个variation的结果并去重"""
    print(f"\n{'='*80}")
    print(f"Merging {db.upper()} variations...")
    print(f"{'='*80}")

    all_dfs = []
    total_meta_count = 0

    id_column = {
        "openalex": "openalex_id",
        "pubmed": "pmid",
        "scopus": "eid"
    }.get(db, "doi")

    for var_result in variation_results:
        if not var_result.get("success"):
            continue

        var_idx = var_result['variation_idx']
        csv_path = var_result['output_files'].get('summary_csv')

        if csv_path and Path(csv_path).exists():
            try:
                df = pd.read_csv(csv_path)
                df['source_variation'] = var_idx
                all_dfs.append(df)
                print(f"  Variation #{var_idx}: {len(df)} records (meta_count: {var_result['meta_count']:,})")
                total_meta_count = max(total_meta_count, var_result['meta_count'])
            except Exception as e:
                logger.warning(f"Failed to read CSV from variation {var_idx}: {e}")

    if not all_dfs:
        return {
            "success": False,
            "error": "No data to merge",
            "final_count": 0,
            "duplicates_removed": 0
        }

    # Merge
    merged_df = pd.concat(all_dfs, ignore_index=True)
    before_dedup = len(merged_df)

    # Deduplicate
    if id_column in merged_df.columns:
        merged_df = merged_df.dropna(subset=[id_column])
        merged_df = merged_df.drop_duplicates(subset=[id_column], keep='first')
    elif 'doi' in merged_df.columns:
        merged_df = merged_df.dropna(subset=['doi'])
        merged_df['doi_normalized'] = merged_df['doi'].str.lower().str.strip()
        merged_df = merged_df.drop_duplicates(subset=['doi_normalized'], keep='first')
        merged_df = merged_df.drop(columns=['doi_normalized'])
    else:
        if 'title' in merged_df.columns:
            merged_df = merged_df.drop_duplicates(subset=['title'], keep='first')

    after_dedup = len(merged_df)
    duplicates = before_dedup - after_dedup

    print(f"\n  📊 Merge Summary:")
    print(f"     Total retrieved:      {before_dedup:>6,}")
    print(f"     Duplicates removed:   {duplicates:>6,}")
    print(f"     Final unique:         {after_dedup:>6,}")
    print(f"     Dedup rate:           {duplicates/before_dedup*100:>6.1f}%")

    # Save merged results
    merged_out_dir = Path(base_out_dir)
    merged_out_dir.mkdir(parents=True, exist_ok=True)

    merged_csv = merged_out_dir / "works_summary_merged.csv"
    merged_df.to_csv(merged_csv, index=False)

    return {
        "success": True,
        "final_count": after_dedup,
        "total_before_dedup": before_dedup,
        "duplicates_removed": duplicates,
        "dedup_rate": duplicates/before_dedup*100 if before_dedup > 0 else 0,
        "meta_count": total_meta_count,
        "merged_csv": str(merged_csv)
    }

def test_topic(provider, topic_key: str, topic: str, databases: List[str], max_results: int = 50) -> Dict:
    """完整测试一个主题的5-variation workflow"""
    print_section(f"TESTING: {topic_key.upper()}")

    # Step 1: Generate 5 variations
    variations = generate_variations(provider, topic_key, topic, num_variations=5)

    if not variations:
        return {"success": False, "error": "Failed to generate variations"}

    print(f"\n✅ Generated {len(variations)} variations")

    # Step 2: Search each variation for each database
    base_out_dir = f"test_variations_{topic_key}_{datetime.now().strftime('%H%M%S')}"

    results = {}

    for db in databases:
        print_section(f"{db.upper()}: Searching All Variations")

        db_out_dir = f"{base_out_dir}/{db}"
        variation_results = []

        for variation in variations:
            var_idx = variation['variation_seed']
            print(f"\n  Searching Variation #{var_idx}...")

            result = search_single_variation(db, variation, max_results, db_out_dir)
            variation_results.append(result)

            if result['success']:
                print(f"  ✅ Variation #{var_idx}: {result['meta_count']:,} total matches (retrieved {result['retrieved']})")
            else:
                print(f"  ❌ Variation #{var_idx}: Failed")

        # Step 3: Merge and deduplicate
        merged_result = merge_variations(db, variation_results, db_out_dir)
        results[db] = merged_result

    return {
        "success": True,
        "topic_key": topic_key,
        "num_variations": len(variations),
        "results": results
    }

def main():
    """主测试流程"""
    print_section("5-Variation Test for Two Research Topics")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Configure provider
    provider_type = os.environ.get("LLM_PROVIDER", "bedrock")

    if provider_type == "bedrock":
        provider = create_llm_provider("bedrock", {
            "region": os.environ.get("AWS_REGION", "us-east-1"),
            "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
        })
    else:
        print("❌ Please set LLM_PROVIDER=bedrock")
        return 1

    if not provider.is_available():
        print("❌ Provider not available")
        return 1

    print(f"✅ Connected to {provider.get_model_name()}")

    # Test databases - now including Scopus
    databases = ["openalex", "pubmed", "scopus"]

    # Test both topics
    all_results = {}

    for topic_key, topic_text in TOPICS.items():
        result = test_topic(provider, topic_key, topic_text, databases, max_results=100)
        all_results[topic_key] = result

    # Final summary
    print_section("FINAL SUMMARY")

    for topic_key, result in all_results.items():
        print(f"\n{topic_key.upper()}:")

        if not result.get("success"):
            print(f"  ❌ Failed: {result.get('error')}")
            continue

        for db, db_result in result['results'].items():
            if db_result.get('success'):
                print(f"\n  {db.upper()}:")
                print(f"    Total retrieved (5 vars): {db_result['total_before_dedup']:>6,}")
                print(f"    Duplicates removed:       {db_result['duplicates_removed']:>6,}")
                print(f"    Final unique count:       {db_result['final_count']:>6,}")
                print(f"    Max meta_count:           {db_result['meta_count']:>6,}")
            else:
                print(f"\n  {db.upper()}: Failed")

    # Save summary
    summary_file = f"variation_test_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(summary_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n\n{'='*100}")
    print(f"Summary saved to: {summary_file}")
    print(f"{'='*100}\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
