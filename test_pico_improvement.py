#!/usr/bin/env python3
"""
Quick test to evaluate PICO framework impact on query robustness.
Runs 5 variations and compares CV to baseline (previous 20-variation test showed CV=378.6%).
"""

import json
import os
import sys
from pathlib import Path
import statistics

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.m1_query_gen import QueryGenerationTeam
from modules.m2_search_exec import SearchExecutor
from utils.llm_providers import BedrockProvider
from utils.logger import get_logger

logger = get_logger()

# Research question from previous robustness test
RESEARCH_QUESTION = """I am interested in research papers that evaluate the causal impact of weather forecast-based interventions on the temperature-health relationship.

INTERVENTION SCOPE:
- Heat warning systems, heat-health action plans, cooling center programs
- Public health advisories based on weather predictions
- Interventions activated by temperature forecasts

STUDY DESIGN: Rigorous causal designs (RCTs, quasi-experimental, natural experiments)
OUTCOMES: Temperature-related mortality/morbidity, heat health impacts
SCOPE: Any country, any population, any time period"""

def run_pico_test(num_variations=5):
    """Run quick PICO framework test."""

    logger.info("=" * 80)
    logger.info("PICO FRAMEWORK ROBUSTNESS TEST")
    logger.info("=" * 80)
    logger.info(f"Running {num_variations} variations with PICO-enhanced agents")
    logger.info("Baseline CV from previous test: 378.6%")
    logger.info("=" * 80)

    # Initialize provider
    try:
        provider = BedrockProvider()
        if not provider.is_available():
            logger.error("AWS Bedrock not available. Please check credentials.")
            return None
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock provider: {e}")
        return None

    # Create output directory
    out_dir = Path("pico_test_results")
    out_dir.mkdir(exist_ok=True)
    queries_dir = out_dir / "queries"
    queries_dir.mkdir(exist_ok=True)
    results_dir = out_dir / "search_results"
    results_dir.mkdir(exist_ok=True)

    # Generate queries
    team = QueryGenerationTeam(llm_provider=provider)
    all_queries = []

    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1: Query Generation")
    logger.info("=" * 80)

    for i in range(1, num_variations + 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Generating Variation {i}/{num_variations}")
        logger.info(f"{'='*60}")

        result = team.generate_queries(RESEARCH_QUESTION, variation_seed=i)

        # Save query
        query_file = queries_dir / f"variation_{i:02d}_queries.json"
        with open(query_file, 'w') as f:
            json.dump(result, f, indent=2)

        all_queries.append({
            'variation': i,
            'queries': result['refiner_queries'],
            'pico': result.get('pulse_pico', {}),
            'pico_statement': result.get('pulse_pico_statement', '')
        })

        logger.info(f"✅ Variation {i} saved to {query_file}")

    # Execute searches on OpenAlex only
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2: Search Execution (OpenAlex only)")
    logger.info("=" * 80)

    result_counts = []

    for i, query_data in enumerate(all_queries, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Searching Variation {i}/{num_variations}")
        logger.info(f"{'='*60}")

        query = query_data['queries']['openalex_query']
        logger.info(f"Query: {query[:100]}...")

        var_dir = results_dir / f"variation_{i:02d}"
        var_dir.mkdir(exist_ok=True)

        executor = SearchExecutor(
            database='openalex',
            query=query,
            config={}
        )

        try:
            executor.execute_search(max_results=100, out_dir=str(var_dir))

            # Read result count
            summary_file = var_dir / 'openalex' / 'run_summary.json'
            if summary_file.exists():
                with open(summary_file) as f:
                    summary = json.load(f)
                    count = summary.get('meta_count', 0)
                    result_counts.append(count)
                    logger.info(f"✅ Retrieved {count} papers")
            else:
                logger.warning(f"⚠️ No summary file found for variation {i}")
                result_counts.append(0)

        except Exception as e:
            logger.error(f"❌ Search failed for variation {i}: {e}")
            result_counts.append(0)

    # Calculate statistics
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 3: Statistical Analysis")
    logger.info("=" * 80)

    if len(result_counts) < 2:
        logger.error("Not enough results for statistical analysis")
        return None

    mean_count = statistics.mean(result_counts)
    std_count = statistics.stdev(result_counts) if len(result_counts) > 1 else 0
    cv = (std_count / mean_count * 100) if mean_count > 0 else float('inf')

    stats = {
        'num_variations': num_variations,
        'result_counts': result_counts,
        'min': int(min(result_counts)),
        'max': int(max(result_counts)),
        'mean': float(mean_count),
        'median': float(statistics.median(result_counts)),
        'std': float(std_count),
        'cv_percent': float(cv),
        'range_ratio': float(max(result_counts) / min(result_counts)) if min(result_counts) > 0 else float('inf'),
        'baseline_cv': 378.6,
        'improvement_percent': float(((378.6 - cv) / 378.6) * 100) if cv < 378.6 else 0
    }

    # Save statistics
    stats_file = out_dir / 'test_statistics.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print results
    logger.info("\n📊 RESULTS:")
    logger.info(f"   Result counts: {result_counts}")
    logger.info(f"   Min: {stats['min']}")
    logger.info(f"   Max: {stats['max']}")
    logger.info(f"   Mean: {stats['mean']:.1f}")
    logger.info(f"   Median: {stats['median']:.1f}")
    logger.info(f"   Std Dev: {stats['std']:.1f}")
    logger.info(f"   CV: {stats['cv_percent']:.1f}%")
    logger.info(f"   Range ratio: {stats['range_ratio']:.1f}:1")
    logger.info("")
    logger.info(f"📈 COMPARISON TO BASELINE:")
    logger.info(f"   Baseline CV (no PICO): 378.6%")
    logger.info(f"   New CV (with PICO): {stats['cv_percent']:.1f}%")

    if stats['cv_percent'] < 378.6:
        improvement = stats['improvement_percent']
        logger.info(f"   ✅ IMPROVEMENT: {improvement:.1f}% reduction in variability")
    elif stats['cv_percent'] > 378.6:
        degradation = ((stats['cv_percent'] - 378.6) / 378.6) * 100
        logger.info(f"   ❌ DEGRADATION: {degradation:.1f}% increase in variability")
    else:
        logger.info(f"   ⚖️  No change in variability")

    logger.info(f"\n📁 Results saved to: {out_dir}")

    return stats

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test PICO framework impact on query robustness')
    parser.add_argument('--num-variations', type=int, default=5,
                        help='Number of variations to test (default: 5)')

    args = parser.parse_args()

    stats = run_pico_test(num_variations=args.num_variations)

    if stats:
        print("\n" + "=" * 80)
        print("TEST COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print(f"CV Improvement: {stats['improvement_percent']:.1f}%")
        print(f"Results saved to: pico_test_results/")
    else:
        print("\n" + "=" * 80)
        print("TEST FAILED")
        print("=" * 80)
        sys.exit(1)
