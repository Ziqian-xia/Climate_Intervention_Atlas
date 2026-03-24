#!/usr/bin/env python3
"""
简化的测试 - 使用更宽松的查询（基于实际的Phase 1输出）
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from modules.m2_search_exec import SearchExecutor
from utils.logger import get_logger

logger = get_logger()

def test_with_actual_phase1_query():
    """使用实际Phase 1的输出进行测试"""
    print("="*80)
    print("使用实际Phase 1生成的查询进行测试")
    print("="*80)

    # 这是从之前的search_results_20260323_221624中提取的实际查询
    actual_queries = {
        "openalex": '("weather forecast" OR "heat forecast" OR "heat warning" OR "heat alert" OR "extreme heat alert" OR "heat action plan" OR "heat health warning system" OR "early warning system" OR "heatwave warning" OR "heat wave warning" OR "temperature forecast" OR "meteorological forecast") AND ("heat-related illness" OR "heat-related mortality" OR "heat-related morbidity" OR "heat stroke" OR "hyperthermia" OR "excess mortality" OR "temperature-mortality" OR "temperature-morbidity" OR "extreme heat" OR "heatwave" OR "heat wave") AND ("causal inference" OR "quasi-experimental" OR "difference-in-differences" OR "regression discontinuity" OR "instrumental variable" OR "natural experiment" OR "treatment effect" OR "counterfactual" OR "impact evaluation" OR "forecast accuracy" OR "behavioral response" OR "protective behavior" OR "heat adaptation" OR "public health intervention")',

        "pubmed": '(("weather forecast"[Title/Abstract] OR "heat forecast"[Title/Abstract] OR "heat warning"[Title/Abstract] OR "heat alert"[Title/Abstract] OR "extreme heat alert"[Title/Abstract] OR "heat action plan"[Title/Abstract] OR "heat health warning system"[Title/Abstract] OR "heatwave warning"[Title/Abstract] OR "heat wave warning"[Title/Abstract] OR "temperature forecast"[Title/Abstract] OR "meteorological forecast"[Title/Abstract] OR "early warning system"[Title/Abstract] OR "Early Warning Systems"[MeSH Terms]) AND ("heat-related illness"[Title/Abstract] OR "heat-related mortality"[Title/Abstract] OR "heat-related morbidity"[Title/Abstract] OR "heat stroke"[Title/Abstract] OR "hyperthermia"[Title/Abstract] OR "excess mortality"[Title/Abstract] OR "temperature-mortality"[Title/Abstract] OR "temperature-morbidity"[Title/Abstract] OR "extreme heat"[Title/Abstract] OR "heatwave"[Title/Abstract] OR "heat wave"[Title/Abstract] OR "Heat Stress Disorders"[MeSH Terms] OR "Hot Temperature"[MeSH Terms]) AND ("causal inference"[Title/Abstract] OR "randomized controlled trial"[Title/Abstract] OR "quasi-experimental"[Title/Abstract] OR "difference-in-differences"[Title/Abstract] OR "regression discontinuity"[Title/Abstract] OR "instrumental variable"[Title/Abstract] OR "natural experiment"[Title/Abstract] OR "treatment effect"[Title/Abstract] OR "counterfactual"[Title/Abstract] OR "plausibly exogenous"[Title/Abstract] OR "impact evaluation"[Title/Abstract] OR "forecast accuracy"[Title/Abstract] OR "behavioral response"[Title/Abstract] OR "protective behavior"[Title/Abstract] OR "heat adaptation"[Title/Abstract] OR "public health intervention"[Title/Abstract] OR "Public Health Surveillance"[MeSH Terms]))',

        "scopus": 'TITLE-ABS-KEY(("weather forecast*" OR "heat forecast*" OR "heat warning*" OR "heat alert*" OR "extreme heat alert*" OR "heat action plan*" OR "heat health warning system*" OR "heatwave warning*" OR "heat wave warning*" OR "temperature forecast*" OR "meteorological forecast*" OR "early warning system*") AND ("heat-related illness" OR "heat-related mortality" OR "heat-related morbidity" OR "heat stroke" OR "hyperthermia" OR "excess mortality" OR "temperature-mortality" OR "temperature-morbidity" OR "extreme heat" OR "heatwave" OR "heat wave") AND ("causal inference" OR "randomized controlled trial" OR "quasi-experimental" OR "difference-in-differences" OR "regression discontinuity" OR "instrumental variable*" OR "natural experiment*" OR "treatment effect*" OR "counterfactual" OR "plausibly exogenous" OR "impact evaluation" OR "forecast accuracy" OR "behavioral response" OR "protective behavior" OR "heat adaptation" OR "public health intervention*"))'
    }

    print("\n查询说明:")
    print("  - 这是基于用户实际研究主题的Phase 1生成的查询")
    print("  - 包含多个同义词和相关概念")
    print("  - 使用OR扩展覆盖范围，AND连接核心概念")

    results = {}

    # Test each database
    for db in ["openalex", "pubmed", "scopus"]:
        print(f"\n{'='*80}")
        print(f"测试 {db.upper()}")
        print(f"{'='*80}")

        config = {
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
        }[db]

        query = actual_queries[db]
        print(f"查询长度: {len(query)} 字符")
        print(f"查询预览: {query[:100]}...")

        try:
            executor = SearchExecutor(db, query, config)
            out_dir = f"test_actual_{db}_{datetime.now().strftime('%H%M%S')}"
            result = executor.execute_search(max_results=20, out_dir=out_dir)

            # Read summary
            with open(f"{out_dir}/run_summary.json") as f:
                summary = json.load(f)

            results[db] = {
                "success": result.get("success"),
                "meta_count": summary.get("meta_count", result.get("results_count", 0)),
                "retrieved": result.get("results_count", 0)
            }

            if result.get("success"):
                print(f"\n✅ 成功")
                print(f"   总匹配数: {results[db]['meta_count']:,}")
                print(f"   已获取: {results[db]['retrieved']}")
            else:
                print(f"\n❌ 失败: {result.get('error', 'Unknown')[:100]}")

        except Exception as e:
            print(f"\n❌ 异常: {str(e)[:100]}")
            results[db] = {"success": False, "meta_count": 0, "retrieved": 0}

    # Analysis
    print(f"\n{'='*80}")
    print("结果分析")
    print(f"{'='*80}")

    print(f"\n总匹配数对比:")
    for db in ["openalex", "pubmed", "scopus"]:
        if results[db]["success"]:
            print(f"  {db.upper():10} : {results[db]['meta_count']:>8,} 条")
        else:
            print(f"  {db.upper():10} : {'FAILED':>8}")

    # Check if results are reasonable
    oa_count = results["openalex"]["meta_count"]
    pm_count = results["pubmed"]["meta_count"]
    sc_count = results["scopus"]["meta_count"]

    print(f"\n一致性评估:")

    if oa_count > 0 and pm_count > 0:
        ratio = oa_count / pm_count
        print(f"  OpenAlex/PubMed比率: {ratio:.1f}x")
        if ratio >= 1.0:
            print(f"  ✅ OpenAlex返回更多或接近结果（符合预期）")
        else:
            print(f"  ⚠️  OpenAlex返回更少结果（可能有问题）")

    if all([oa_count > 0, pm_count > 0, sc_count > 0]):
        max_count = max(oa_count, pm_count, sc_count)
        min_count = min(oa_count, pm_count, sc_count)
        spread = max_count / min_count

        print(f"  最大/最小比率: {spread:.1f}x")
        if spread < 10:
            print(f"  ✅ 结果在合理范围内（<10倍差异）")
        elif spread < 50:
            print(f"  ⚠️  结果差异较大（10-50倍）")
        else:
            print(f"  ❌ 结果差异过大（>50倍）")

    # Final verdict
    print(f"\n{'='*80}")
    all_success = all(r["success"] for r in results.values())
    reasonable_counts = (
        oa_count >= pm_count * 0.5 and  # OpenAlex不应该比PubMed少太多
        oa_count > 0 and  # OpenAlex应该有结果
        (max(oa_count, pm_count, sc_count) / min(oa_count, pm_count, sc_count) < 100 if all([oa_count, pm_count, sc_count]) else True)
    )

    if all_success and reasonable_counts:
        print("✅ 测试通过 - 可以进行UI测试")
        print("\n推荐操作:")
        print("  1. 访问 http://localhost:8501")
        print("  2. 硬刷新 (Cmd+Shift+R)")
        print("  3. 运行Phase 2搜索")
        print("  4. 验证结果与此测试一致")
        return 0
    else:
        print("❌ 测试未完全通过")
        if not all_success:
            print("  - 部分数据库失败")
        if not reasonable_counts:
            print("  - 结果数量不合理")
        return 1

if __name__ == "__main__":
    sys.exit(test_with_actual_phase1_query())
