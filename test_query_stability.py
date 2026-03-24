#!/usr/bin/env python3
"""
测试查询稳定性 - 使用相同prompt多次运行Phase 1+2，分析结果差异

目的：
1. 验证Phase 1生成查询的一致性
2. 测试Phase 2搜索结果的稳定性
3. 找出结果数量差异的根本原因
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from modules.m1_query_gen import QueryGenerationTeam
from modules.m2_search_exec import SearchExecutor
from utils.llm_providers import create_llm_provider
from utils.logger import get_logger

logger = get_logger()

# 用户的实际研究主题
USER_TOPIC = """I am interested in research papers on the impacts of weather forecasts interventions on the temperature–health relationship. I am specifically interested in papers with causal research designs—i.e., papers that can isolate the impact of plausibly random assignment (experimental or quasi-experimental) of cooling centers to a population of interest. Papers from anywhere in the world on any population would be of interest."""

def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

def run_phase1(provider, iteration: int) -> Dict:
    """运行Phase 1查询生成"""
    print_section(f"Run #{iteration}: Phase 1 - Query Generation")

    team = QueryGenerationTeam(llm_provider=provider)
    result = team.generate_queries(USER_TOPIC)

    # Extract final queries from refiner_queries
    refiner_queries = result.get('refiner_queries', {})

    if refiner_queries and refiner_queries.get('openalex_query'):
        print(f"✅ Query generation successful")
        print(f"\nElsevier Query Length: {len(refiner_queries['elsevier_query'])} chars")
        print(f"PubMed Query Length: {len(refiner_queries['pubmed_query'])} chars")
        print(f"OpenAlex Query Length: {len(refiner_queries['openalex_query'])} chars")

        # 显示查询预览
        print(f"\nOpenAlex Query Preview:")
        print(f"  {refiner_queries['openalex_query'][:150]}...")

        # Add success flag and flatten queries for compatibility
        result['success'] = True
        result['elsevier_query'] = refiner_queries['elsevier_query']
        result['pubmed_query'] = refiner_queries['pubmed_query']
        result['openalex_query'] = refiner_queries['openalex_query']
    else:
        print(f"❌ Query generation failed or incomplete")
        result['success'] = False
        result['elsevier_query'] = ''
        result['pubmed_query'] = ''
        result['openalex_query'] = ''

    return result

def run_phase2(queries: Dict, iteration: int, max_results: int = 50) -> Dict:
    """运行Phase 2搜索执行（只获取少量结果用于测试）"""
    print_section(f"Run #{iteration}: Phase 2 - Search Execution")

    results = {}

    # 测试配置
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
        "openalex": queries.get("openalex_query"),
        "pubmed": queries.get("pubmed_query"),
        "scopus": queries.get("elsevier_query")  # Scopus uses Elsevier query
    }

    for db in ["openalex", "pubmed", "scopus"]:
        print(f"\n{'='*80}")
        print(f"Testing {db.upper()}")
        print(f"{'='*80}")

        query = query_map[db]
        config = configs[db]

        if not query:
            print(f"⚠️ No query generated for {db}")
            results[db] = {"success": False, "error": "No query"}
            continue

        print(f"Query length: {len(query)} chars")
        print(f"Query preview: {query[:100]}...")

        try:
            executor = SearchExecutor(db, query, config)
            out_dir = f"test_stability_{db}_run{iteration}_{datetime.now().strftime('%H%M%S')}"

            result = executor.execute_search(max_results=max_results, out_dir=out_dir)

            # 读取summary获取meta_count
            summary_file = Path(out_dir) / "run_summary.json"
            if summary_file.exists():
                with open(summary_file) as f:
                    summary = json.load(f)
                    meta_count = summary.get("meta_count", 0)
            else:
                meta_count = result.get("results_count", 0)

            results[db] = {
                "success": result.get("success"),
                "meta_count": meta_count,
                "retrieved": result.get("results_count", 0),
                "status": result.get("status"),
                "query": query,
                "out_dir": out_dir
            }

            if result.get("success"):
                print(f"✅ {db.upper()}: {meta_count:,} total matches (retrieved {result.get('results_count')})")
            else:
                print(f"❌ {db.upper()} failed: {result.get('error', 'Unknown')[:100]}")

        except Exception as e:
            print(f"❌ {db.upper()} exception: {str(e)[:100]}")
            results[db] = {
                "success": False,
                "meta_count": 0,
                "retrieved": 0,
                "error": str(e),
                "query": query
            }

    return results

def compare_runs(all_runs: List[Dict]):
    """比较多次运行的差异"""
    print_section("Cross-Run Analysis")

    # 1. 查询一致性分析
    print("\n📊 Query Consistency Analysis")
    print("-" * 100)

    for db in ["openalex", "pubmed", "scopus"]:
        print(f"\n{db.upper()} Queries:")
        query_key = f'{db}_query' if db != 'scopus' else 'elsevier_query'
        queries = [run['phase1'][query_key]
                   for run in all_runs if run['phase1'].get('success') and run['phase1'].get(query_key)]

        if not queries:
            print("  No successful queries")
            continue

        # 检查查询是否完全相同
        unique_queries = list(set(queries))

        if len(unique_queries) == 1:
            print(f"  ✅ All queries IDENTICAL ({len(queries)} runs)")
        else:
            print(f"  ⚠️  {len(unique_queries)} DIFFERENT queries across {len(queries)} runs")
            print(f"  Query lengths: {[len(q) for q in unique_queries]}")

            # 显示查询差异
            for i, q in enumerate(unique_queries, 1):
                print(f"\n  Variant {i} (length {len(q)}):")
                print(f"    {q[:150]}...")

    # 2. 搜索结果数量分析
    print("\n\n📊 Search Results Count Analysis")
    print("-" * 100)

    for db in ["openalex", "pubmed", "scopus"]:
        print(f"\n{db.upper()} Results:")

        counts = []
        for i, run in enumerate(all_runs, 1):
            if run['phase2'][db].get('success'):
                count = run['phase2'][db]['meta_count']
                counts.append(count)
                print(f"  Run {i}: {count:>8,} matches")
            else:
                print(f"  Run {i}: {'FAILED':>8}")

        if counts:
            min_count = min(counts)
            max_count = max(counts)
            avg_count = sum(counts) / len(counts)

            print(f"\n  Statistics:")
            print(f"    Min:     {min_count:>8,}")
            print(f"    Max:     {max_count:>8,}")
            print(f"    Average: {avg_count:>8,.0f}")

            if min_count > 0:
                variance = (max_count - min_count) / min_count * 100
                print(f"    Variance: {variance:>7.1f}%")

                if variance < 5:
                    print(f"    ✅ STABLE (variance < 5%)")
                elif variance < 20:
                    print(f"    ⚠️  MODERATE variance (5-20%)")
                else:
                    print(f"    ❌ HIGH variance (>20%)")

    # 3. 查询-结果相关性
    print("\n\n📊 Query-Result Correlation")
    print("-" * 100)

    for db in ["openalex", "pubmed", "scopus"]:
        print(f"\n{db.upper()}:")

        query_result_pairs = []
        for run in all_runs:
            if run['phase1'].get('success') and run['phase2'].get(db, {}).get('success'):
                query_key = f"{db}_query" if db != "scopus" else "elsevier_query"
                query = run['phase1'].get(query_key, '')
                if query:
                    count = run['phase2'][db]['meta_count']
                    query_result_pairs.append((query, count))

        if not query_result_pairs:
            print("  No data")
            continue

        # 按查询分组统计
        query_groups = {}
        for query, count in query_result_pairs:
            if query not in query_groups:
                query_groups[query] = []
            query_groups[query].append(count)

        print(f"  {len(query_groups)} unique queries generated {len(query_result_pairs)} results")

        if len(query_groups) > 1:
            print(f"\n  Different queries → different results:")
            for i, (query, counts) in enumerate(query_groups.items(), 1):
                avg = sum(counts) / len(counts)
                print(f"    Query variant {i}: avg {avg:,.0f} results (n={len(counts)} runs)")
                print(f"      {query[:100]}...")
        else:
            print(f"  ✅ Same query used in all runs")
            counts = list(query_groups.values())[0]
            if len(set(counts)) == 1:
                print(f"  ✅ Same query → same results ({counts[0]:,})")
            else:
                print(f"  ⚠️  Same query → different results: {counts}")

def main():
    """主测试流程"""
    print_section("Query Stability Test - Multiple Runs with Same Topic")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nTopic:\n{USER_TOPIC}\n")

    # 配置LLM provider
    provider_type = os.environ.get("LLM_PROVIDER", "bedrock")

    print(f"Using LLM provider: {provider_type}")

    if provider_type == "anthropic":
        provider = create_llm_provider("anthropic", {
            "api_key": os.environ.get("ANTHROPIC_API_KEY")
        })
    elif provider_type == "bedrock":
        provider = create_llm_provider("bedrock", {
            "region": os.environ.get("AWS_REGION", "us-east-1"),
            "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
        })
    else:
        print("❌ Unknown provider. Set LLM_PROVIDER environment variable.")
        return 1

    if not provider.is_available():
        print("❌ LLM provider not available. Check credentials.")
        return 1

    print(f"✅ Connected to {provider.get_model_name()}")

    # 运行次数
    num_runs = int(input("\nHow many test runs? (recommended: 3-5): "))

    all_runs = []

    for i in range(1, num_runs + 1):
        print(f"\n\n{'#'*100}")
        print(f"# RUN {i} of {num_runs}")
        print(f"{'#'*100}")

        # Phase 1: Generate queries
        phase1_result = run_phase1(provider, i)

        if not phase1_result.get("success"):
            print(f"❌ Run {i} Phase 1 failed, skipping Phase 2")
            all_runs.append({
                "iteration": i,
                "phase1": phase1_result,
                "phase2": {}
            })
            continue

        # Phase 2: Execute searches
        phase2_result = run_phase2(phase1_result, i, max_results=20)

        all_runs.append({
            "iteration": i,
            "phase1": phase1_result,
            "phase2": phase2_result
        })

        # 每次运行后显示当前结果
        print(f"\n{'='*80}")
        print(f"Run {i} Summary:")
        print(f"{'='*80}")
        for db in ["openalex", "pubmed", "scopus"]:
            if phase2_result[db].get("success"):
                count = phase2_result[db]['meta_count']
                print(f"  {db.upper():10}: {count:>8,} matches")
            else:
                print(f"  {db.upper():10}: {'FAILED':>8}")

    # 比较所有运行
    if len(all_runs) > 1:
        compare_runs(all_runs)

    # 保存完整结果
    report_file = f"stability_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(all_runs, f, indent=2)

    print(f"\n\n{'='*100}")
    print(f"Full report saved to: {report_file}")
    print(f"{'='*100}\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
