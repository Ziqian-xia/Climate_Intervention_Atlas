#!/usr/bin/env python3
"""
PICO Framework Integration Test
Demonstrates PICO-based query generation without API calls (dummy mode)
"""

import json
from modules.m1_query_gen import QueryGenerationTeam

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_pico_query_generation():
    """Test PICO-based query generation in dummy mode"""

    print("\n" + "🎯 PICO Framework Integration Test")
    print("Using dummy mode (no API calls required)")

    # Initialize query generation team without LLM provider (dummy mode)
    query_team = QueryGenerationTeam(llm_provider=None)

    # Test topic
    topic = "cooling centers and heat-related mortality in elderly populations"

    print_section("INPUT")
    print(f"Research Topic: {topic}")

    # Generate queries using PICO framework
    result = query_team.generate_queries(topic)

    # Display PICO structure from Pulse Agent
    print_section("PULSE AGENT - PICO ANALYSIS")

    pico = result.get('pulse_pico', {})
    print("\n📍 PICO Components:")
    print(f"\n  P (Population):")
    for keyword in pico.get('population', []):
        print(f"    - {keyword}")

    print(f"\n  I (Intervention):")
    for keyword in pico.get('intervention', []):
        print(f"    - {keyword}")

    print(f"\n  C (Comparison):")
    comparison = pico.get('comparison', [])
    if comparison:
        for keyword in comparison:
            print(f"    - {keyword}")
    else:
        print(f"    - (Not applicable)")

    print(f"\n  O (Outcome):")
    for keyword in pico.get('outcome', []):
        print(f"    - {keyword}")

    # Study design terms
    print(f"\n📚 Study Design Terms:")
    for keyword in result.get('pulse_study_design', []):
        print(f"  - {keyword}")

    # PICO statement
    print_section("STRUCTURED RESEARCH QUESTION")
    pico_statement = result.get('pulse_pico_statement', '')
    print(f"\n{pico_statement}")

    # Reasoning
    print_section("PULSE REASONING")
    print(f"\n{result.get('pulse_reasoning', '')}")

    # Formulator's PICO-structured queries
    print_section("FORMULATOR - PICO-STRUCTURED QUERIES")

    formulator_pico = result.get('formulator_pico_structure', {})
    print("\n📊 PICO Structure Used in Queries:")
    print(f"\n  Population: {formulator_pico.get('population', 'N/A')}")
    print(f"  Intervention: {formulator_pico.get('intervention', 'N/A')}")
    print(f"  Comparison: {formulator_pico.get('comparison', 'N/A')}")
    print(f"  Outcome: {formulator_pico.get('outcome', 'N/A')}")

    # Display queries
    refiner_queries = result.get('refiner_queries', {})

    print("\n🔍 Generated Queries:")

    print("\n1. Elsevier/Scopus Query:")
    print("-" * 70)
    print(refiner_queries.get('elsevier_query', ''))

    print("\n2. PubMed Query:")
    print("-" * 70)
    print(refiner_queries.get('pubmed_query', ''))

    print("\n3. OpenAlex Query:")
    print("-" * 70)
    print(refiner_queries.get('openalex_query', ''))

    # Formulator reasoning
    print_section("FORMULATOR REASONING")
    print(f"\n{result.get('formulator_reasoning', '')}")

    # Export full result as JSON
    print_section("FULL RESULT (JSON)")
    print("\nExporting to: pico_test_result.json")
    with open('pico_test_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print("✅ Exported successfully!")

    # Summary
    print_section("SUMMARY")
    print("\n✅ PICO Framework Integration Test Completed")
    print(f"\n📊 Statistics:")
    print(f"  - Total keywords: {len(result.get('pulse_keywords', []))}")
    print(f"  - Population terms: {len(pico.get('population', []))}")
    print(f"  - Intervention terms: {len(pico.get('intervention', []))}")
    print(f"  - Outcome terms: {len(pico.get('outcome', []))}")
    print(f"  - Study design terms: {len(result.get('pulse_study_design', []))}")
    print(f"  - Databases covered: 3 (Elsevier, PubMed, OpenAlex)")

    print("\n📁 Output files:")
    print("  - pico_test_result.json (full result)")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_pico_query_generation()
