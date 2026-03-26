#!/bin/bash
# Wait for PICO test to complete and display results

echo "⏳ Waiting for PICO improvement test to complete..."
echo ""

while true; do
    if ps aux | grep -v grep | grep "test_pico_improvement.py" > /dev/null; then
        # Test is still running
        sleep 30
        echo -n "."
    else
        # Test finished
        echo ""
        echo ""
        echo "✅ Test completed!"
        echo ""

        if [ -f "pico_test_results/test_statistics.json" ]; then
            echo "=========================================="
            echo "PICO FRAMEWORK TEST RESULTS"
            echo "=========================================="
            echo ""

            python3 -c "
import json

with open('pico_test_results/test_statistics.json') as f:
    stats = json.load(f)

print(f\"📊 Result Counts: {stats['result_counts']}\")
print(f\"   Min: {stats['min']}\")
print(f\"   Max: {stats['max']}\")
print(f\"   Mean: {stats['mean']:.1f}\")
print(f\"   Median: {stats['median']:.1f}\")
print(f\"   Std Dev: {stats['std']:.1f}\")
print(f\"   Range Ratio: {stats['range_ratio']:.1f}:1\")
print()
print(f\"📈 Coefficient of Variation:\")
print(f\"   Baseline (no PICO): {stats['baseline_cv']}%\")
print(f\"   With PICO: {stats['cv_percent']:.1f}%\")
print()

if stats['cv_percent'] < stats['baseline_cv']:
    improvement = stats['improvement_percent']
    print(f\"✅ SUCCESS! {improvement:.1f}% reduction in variability\")
    print()
    if improvement > 75:
        print(\"   🎉 Excellent improvement! PICO framework is highly effective.\")
    elif improvement > 50:
        print(\"   👍 Good improvement! PICO framework shows promise.\")
    elif improvement > 25:
        print(\"   ✓ Moderate improvement. Consider additional refinements.\")
    else:
        print(\"   ⚠️  Slight improvement. May need further optimization.\")
else:
    degradation = ((stats['cv_percent'] - stats['baseline_cv']) / stats['baseline_cv']) * 100
    print(f\"❌ No improvement: {degradation:.1f}% increase in variability\")
    print(\"   Need to investigate failure modes and refine approach.\")
"

            echo ""
            echo "=========================================="
            echo "Detailed results: pico_test_results/test_statistics.json"
            echo "Log file: pico_test_run2.log"
            echo "=========================================="
        else
            echo "❌ Test failed - no results file generated"
            echo ""
            echo "Check log file for errors:"
            echo "  tail -50 pico_test_run2.log"
        fi

        break
    fi
done
