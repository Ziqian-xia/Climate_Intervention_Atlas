#!/bin/bash
# Real-time progress monitoring by checking generated files

RESULTS_DIR="robustness_test_results_20260325_194108"

echo "=========================================="
echo "ROBUSTNESS TEST - Real-time Progress"
echo "=========================================="
echo ""

# Check if process is running
if ps aux | grep -q "[t]est_robustness_20runs.py"; then
    echo "✅ Test process is RUNNING"
    echo ""
else
    echo "⚠️  Test process NOT found"
    echo ""
fi

# Count query variations generated
QUERY_COUNT=$(ls -1 "$RESULTS_DIR/queries/variation_"*.json 2>/dev/null | wc -l | tr -d ' ')
echo "📝 Query Variations: $QUERY_COUNT/20"

if [ $QUERY_COUNT -gt 0 ]; then
    echo ""
    echo "Latest variations:"
    ls -lht "$RESULTS_DIR/queries/variation_"*.json 2>/dev/null | head -5 | awk '{print "  " $9 " - " $6 " " $7 " " $8}'
fi

# Count searches completed
SEARCH_COUNT=$(find "$RESULTS_DIR/search_results" -name "run_summary.json" 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "🔍 Searches Completed: $SEARCH_COUNT/20"

if [ $SEARCH_COUNT -gt 0 ]; then
    echo ""
    echo "Search results (meta_count = total matches):"
    for summary in $(find "$RESULTS_DIR/search_results" -name "run_summary.json" -type f 2>/dev/null | sort); do
        DIR_NAME=$(dirname "$summary" | xargs basename)
        META_COUNT=$(grep -o '"meta_count": [0-9]*' "$summary" 2>/dev/null | cut -d' ' -f2)
        RESULTS_COUNT=$(grep -o '"results_count": [0-9]*' "$summary" 2>/dev/null | cut -d' ' -f2)
        STATUS=$(grep -o '"status": "[^"]*"' "$summary" 2>/dev/null | cut -d'"' -f4)
        echo "  $DIR_NAME: meta_count=$META_COUNT, downloaded=$RESULTS_COUNT, status=$STATUS"
    done
fi

# Check if analysis exists
if [ -f "$RESULTS_DIR/analysis/openalex/result_statistics.json" ]; then
    echo ""
    echo "📊 Analysis completed!"
    cat "$RESULTS_DIR/analysis/openalex/result_statistics.json" | python3 -m json.tool 2>/dev/null | grep -E "min_results|max_results|mean_results|coefficient_of_variation"
fi

echo ""
echo "=========================================="
echo "Run again: bash watch_progress.sh"
