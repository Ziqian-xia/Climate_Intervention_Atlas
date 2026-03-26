#!/bin/bash
# Monitor PICO improvement test progress

echo "==================================="
echo "PICO Framework Test Monitor"
echo "==================================="
echo ""

# Check if test is still running
if ps aux | grep -v grep | grep "test_pico_improvement.py" > /dev/null; then
    echo "✅ Test is RUNNING"
    echo ""

    # Check progress
    echo "📊 Progress:"
    echo ""

    # Count generated queries
    query_count=$(find pico_test_results/queries -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "   Queries generated: $query_count/5"

    # Count completed searches
    search_count=$(find pico_test_results/search_results -name "run_summary.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "   Searches completed: $search_count/5"

    echo ""
    echo "📝 Latest log entries:"
    tail -10 pico_test_run.log 2>/dev/null || echo "   (log file not found)"

else
    echo "⏹️  Test is NOT RUNNING"
    echo ""

    if [ -f "pico_test_results/test_statistics.json" ]; then
        echo "✅ Test COMPLETED - Results available!"
        echo ""
        echo "📊 Results:"
        python3 -c "
import json
with open('pico_test_results/test_statistics.json') as f:
    stats = json.load(f)
    print(f\"   Variations tested: {stats['num_variations']}\")
    print(f\"   Result counts: {stats['result_counts']}\")
    print(f\"   CV: {stats['cv_percent']:.1f}%\")
    print(f\"   Baseline CV: {stats['baseline_cv']}%\")
    if stats['cv_percent'] < stats['baseline_cv']:
        print(f\"   ✅ IMPROVEMENT: {stats['improvement_percent']:.1f}% reduction\")
    else:
        print(f\"   ❌ No improvement\")
" 2>/dev/null || echo "   (Could not parse results)"
    else
        echo "❌ Test did not complete successfully"
        echo ""
        echo "Last log entries:"
        tail -20 pico_test_run.log 2>/dev/null || echo "   (log file not found)"
    fi
fi

echo ""
echo "==================================="
