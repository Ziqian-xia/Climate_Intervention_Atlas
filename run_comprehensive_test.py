#!/usr/bin/env python3
"""
完整的后台检索测试 - 使用用户的实际研究主题
测试所有三个数据库，验证查询语义一致性
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.m2_search_exec import SearchExecutor
from utils.logger import get_logger

logger = get_logger()

def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def run_phase1_simulation():
    """模拟Phase 1生成查询（使用用户实际主题）"""
    print_section("PHASE 1: 查询生成（模拟）")

    # 基于用户研究主题的合理查询
    # 主题: weather forecast interventions on cooling centers and temperature-health relationship

    queries = {
        "openalex": '("weather forecast" OR "heat forecast" OR "heat warning" OR "heat alert" OR "early warning") AND ("cooling center" OR "cooling shelter" OR "heat relief center") AND ("temperature" OR "heat") AND "health" AND ("intervention" OR "causal" OR "quasi-experimental" OR "evaluation")',

        "pubmed": '(("weather forecast"[Title/Abstract] OR "heat forecast"[Title/Abstract] OR "heat warning"[Title/Abstract] OR "heat alert"[Title/Abstract] OR "early warning system"[Title/Abstract]) AND ("cooling center"[Title/Abstract] OR "cooling shelter"[Title/Abstract] OR "heat relief center"[Title/Abstract]) AND ("temperature"[Title/Abstract] OR "extreme heat"[Title/Abstract]) AND "health"[Title/Abstract] AND ("intervention"[Title/Abstract] OR "causal"[Title/Abstract] OR "quasi-experimental"[Title/Abstract] OR "evaluation"[Title/Abstract]))',

        "scopus": 'TITLE-ABS-KEY(("weather forecast*" OR "heat forecast*" OR "heat warning*" OR "heat alert*" OR "early warning system*") AND ("cooling center*" OR "cooling shelter*" OR "heat relief center*") AND ("temperature" OR "extreme heat") AND "health" AND ("intervention*" OR "causal" OR "quasi-experimental" OR "evaluation"))'
    }

    print("\n生成的查询:")
    for db, query in queries.items():
        print(f"\n{db.upper()}:")
        print(f"  {query[:100]}...")
        print(f"  (长度: {len(query)} 字符)")

    return queries

def test_database(db_name, query, config):
    """测试单个数据库"""
    print_section(f"{db_name.upper()} 数据库测试")

    print(f"\n配置:")
    for key, value in config.items():
        if value:
            masked = f"{str(value)[:10]}...{str(value)[-4:]}" if len(str(value)) > 14 else value
            print(f"  {key}: {masked}")
        else:
            print(f"  {key}: (未设置)")

    print(f"\n查询: {query[:80]}...")
    print(f"\n执行中...")

    try:
        executor = SearchExecutor(db_name, query, config)
        out_dir = f"test_full_{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        result = executor.execute_search(max_results=20, out_dir=out_dir)

        # 读取详细的run_summary
        summary_file = Path(out_dir) / "run_summary.json"
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
        else:
            summary = {}

        return {
            "success": result.get("success", False),
            "status": result.get("status", "unknown"),
            "results_count": result.get("results_count", 0),
            "meta_count": summary.get("meta_count", result.get("results_count", 0)),
            "error": result.get("error", ""),
            "output_dir": out_dir,
            "output_files": result.get("output_files", {})
        }

    except Exception as e:
        logger.error(f"{db_name} test failed with exception: {e}", exc_info=True)
        return {
            "success": False,
            "status": "exception",
            "results_count": 0,
            "meta_count": 0,
            "error": str(e),
            "output_dir": None,
            "output_files": {}
        }

def check_consistency(results):
    """检查三个数据库的查询语义一致性"""
    print_section("查询语义一致性检查")

    oa_count = results.get("openalex", {}).get("meta_count", 0)
    pm_count = results.get("pubmed", {}).get("meta_count", 0)
    sc_count = results.get("scopus", {}).get("meta_count", 0)

    print(f"\n结果数量对比:")
    print(f"  OpenAlex:  {oa_count:>8,} 条")
    print(f"  Scopus:    {sc_count:>8,} 条")
    print(f"  PubMed:    {pm_count:>8,} 条")

    issues = []

    # 检查1: OpenAlex应该 >= PubMed（更大的数据库）
    if oa_count > 0 and pm_count > 0:
        if oa_count < pm_count * 0.5:  # OpenAlex显著少于PubMed
            issues.append(f"⚠️  OpenAlex ({oa_count}) 显著少于 PubMed ({pm_count}) - 可能有问题")
        else:
            print(f"\n✅ OpenAlex vs PubMed: 比例合理 ({oa_count / pm_count:.1f}x)")

    # 检查2: Scopus应该在OpenAlex和PubMed之间（或最多）
    if all([oa_count > 0, pm_count > 0, sc_count > 0]):
        # 数量级检查（应该在同一数量级）
        max_count = max(oa_count, pm_count, sc_count)
        min_count = min(oa_count, pm_count, sc_count)

        if max_count > min_count * 100:  # 超过100倍差异
            issues.append(f"⚠️  数据库结果差异过大 (最大/最小 = {max_count/min_count:.0f}x)")
        else:
            print(f"✅ 三个数据库结果在合理范围内 (最大/最小 = {max_count/min_count:.1f}x)")

    # 检查3: OpenAlex不应该为0（除非查询极其专业）
    if oa_count == 0:
        issues.append("❌ OpenAlex 返回0条结果 - Boolean查询可能没有正确处理")

    # 检查4: 至少一个数据库应该有结果
    if all([oa_count == 0, pm_count == 0, sc_count == 0]):
        issues.append("❌ 所有数据库都返回0条结果 - 查询可能有问题")

    print(f"\n一致性检查结果:")
    if issues:
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("  ✅ 所有检查通过 - 查询语义一致")
        return True

def verify_boolean_handling(results):
    """验证Boolean查询是否被正确处理"""
    print_section("Boolean查询处理验证")

    oa_count = results.get("openalex", {}).get("meta_count", 0)

    # 如果OpenAlex返回非常少的结果（<5），可能是Boolean没有正确处理
    if oa_count > 0 and oa_count < 5:
        print(f"⚠️  OpenAlex只返回 {oa_count} 条结果")
        print("    这可能表示Boolean查询没有被正确处理")
        print("    预期应该有至少10-50条结果")
        return False
    elif oa_count >= 5:
        print(f"✅ OpenAlex返回 {oa_count} 条结果 - Boolean查询正常处理")
        return True
    else:
        print(f"❌ OpenAlex返回 0 条结果 - Boolean查询可能失败")
        return False

def generate_report(queries, results, consistency_ok, boolean_ok):
    """生成完整的测试报告"""
    print_section("测试报告总结")

    report = {
        "timestamp": datetime.now().isoformat(),
        "queries": queries,
        "results": results,
        "checks": {
            "consistency": consistency_ok,
            "boolean_handling": boolean_ok
        }
    }

    # 统计
    total_databases = 3
    successful_databases = sum(1 for r in results.values() if r.get("success"))

    print(f"\n数据库状态:")
    for db, result in results.items():
        status_emoji = "✅" if result.get("success") else "❌"
        print(f"  {status_emoji} {db.upper()}: {result.get('status')}")
        if not result.get("success"):
            print(f"      错误: {result.get('error', 'Unknown')[:100]}...")

    print(f"\n总体状态:")
    print(f"  成功: {successful_databases}/{total_databases} 数据库")
    print(f"  查询一致性: {'✅ 通过' if consistency_ok else '❌ 失败'}")
    print(f"  Boolean处理: {'✅ 正常' if boolean_ok else '❌ 异常'}")

    # 判断是否可以进行UI测试
    ready_for_ui = (
        successful_databases >= 2 and  # 至少2个数据库成功
        consistency_ok and  # 查询语义一致
        boolean_ok  # Boolean正确处理
    )

    print(f"\n{'='*80}")
    if ready_for_ui:
        print("✅ 测试通过！可以进行UI手动测试")
        print("\n准备就绪的功能:")
        print("  ✅ OpenAlex: Boolean查询正确处理")
        print("  ✅ 查询语义一致性: 三个数据库执行相同逻辑")
        print("  ✅ 结果数量合理: 在预期范围内")
        print("\n下一步:")
        print("  1. 访问 http://localhost:8501")
        print("  2. 硬刷新浏览器 (Cmd+Shift+R)")
        print("  3. 运行Phase 2搜索")
        print("  4. 验证结果")
    else:
        print("❌ 测试未通过 - 需要修复问题后再进行UI测试")
        print("\n发现的问题:")
        if successful_databases < 2:
            print(f"  - 只有 {successful_databases} 个数据库成功（需要至少2个）")
        if not consistency_ok:
            print("  - 查询语义不一致")
        if not boolean_ok:
            print("  - Boolean查询处理异常")
    print(f"{'='*80}\n")

    # 保存报告
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"详细报告已保存: {report_file}")

    return ready_for_ui

def main():
    """主测试流程"""
    print_section("开始完整的后台检索测试")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n测试目标:")
    print("  1. 验证OpenAlex的Boolean查询修复")
    print("  2. 确认三个数据库的查询语义一致")
    print("  3. 检查结果数量合理性")
    print("  4. 评估是否可以进行UI测试")

    # Step 1: 生成查询
    queries = run_phase1_simulation()

    # Step 2: 测试每个数据库
    results = {}

    # Test OpenAlex
    results["openalex"] = test_database(
        "openalex",
        queries["openalex"],
        {
            "api_key": os.environ.get("OPENALEX_API_KEY", ""),
            "mailto": os.environ.get("OPENALEX_MAILTO", "test@example.com")
        }
    )

    # Test PubMed
    results["pubmed"] = test_database(
        "pubmed",
        queries["pubmed"],
        {
            "api_key": os.environ.get("PUBMED_API_KEY", ""),
            "email": os.environ.get("PUBMED_EMAIL", "test@example.com")
        }
    )

    # Test Scopus
    results["scopus"] = test_database(
        "scopus",
        queries["scopus"],
        {
            "api_key": os.environ.get("SCOPUS_API_KEY", ""),
            "inst_token": os.environ.get("SCOPUS_INST_TOKEN", "")
        }
    )

    # Step 3: 检查一致性
    consistency_ok = check_consistency(results)

    # Step 4: 验证Boolean处理
    boolean_ok = verify_boolean_handling(results)

    # Step 5: 生成报告
    ready = generate_report(queries, results, consistency_ok, boolean_ok)

    # Return exit code
    sys.exit(0 if ready else 1)

if __name__ == "__main__":
    main()
