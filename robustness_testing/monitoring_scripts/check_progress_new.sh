#!/bin/bash
# Progress monitoring script for robustness test (OpenAlex only, full results)

OUTPUT_FILE="/private/tmp/claude-501/-Users-ziqianxia-Documents-GitHub-Climate-Intervention-Atlas/b0cfcce8-b42a-420f-8dad-5143242f489c/tasks/bpsgjt830.output"

echo "=========================================="
echo "ROBUSTNESS TEST PROGRESS MONITOR"
echo "Configuration: OpenAlex only, ALL results, DOI-only"
echo "=========================================="
echo ""

# Check if test is running
if ps aux | grep -q "[t]est_robustness_20runs.py"; then
    echo "✅ Test is RUNNING"
else
    echo "⚠️  Test process not found (may have completed or failed)"
fi

echo ""
echo "Latest log entries:"
echo "------------------------------------------"
tail -80 "$OUTPUT_FILE" | grep -E "Variation|PHASE|Complete|Success|Error|✅|❌|OPENALEX|meta_count|results_count" || echo "No progress markers found yet"

echo ""
echo "------------------------------------------"
echo "Full output file: $OUTPUT_FILE"
echo ""
echo "Run this script again to check progress:"
echo "  bash check_progress_new.sh"
echo ""
echo "Or view live output:"
echo "  tail -f $OUTPUT_FILE"
echo ""

# Try to find latest results directory and show statistics
LATEST_DIR=$(find . -name "robustness_test_results_*" -type d 2>/dev/null | sort -r | head -1)
if [ -n "$LATEST_DIR" ]; then
    echo "Latest results directory: $LATEST_DIR"

    # Count completed variations
    QUERY_COUNT=$(find "$LATEST_DIR/queries" -name "variation_*.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "Query variations generated: $QUERY_COUNT/20"

    # Count completed searches
    SEARCH_COUNT=$(find "$LATEST_DIR/search_results" -name "run_summary.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "Searches completed: $SEARCH_COUNT/20"

    # Show result counts if any searches complete
    if [ $SEARCH_COUNT -gt 0 ]; then
        echo ""
        echo "Result counts (meta_count = total matches in database):"
        find "$LATEST_DIR/search_results" -name "run_summary.json" -exec sh -c 'echo -n "  $(dirname {} | xargs basename): "; cat {} | grep -o "\"meta_count\": [0-9]*" | cut -d" " -f2' \;
    fi
fi
