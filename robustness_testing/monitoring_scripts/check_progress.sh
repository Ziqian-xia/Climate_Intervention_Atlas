#!/bin/bash
# Progress monitoring script for robustness test

OUTPUT_FILE="/private/tmp/claude-501/-Users-ziqianxia-Documents-GitHub-Climate-Intervention-Atlas/b0cfcce8-b42a-420f-8dad-5143242f489c/tasks/bffyvvz1s.output"

echo "=========================================="
echo "ROBUSTNESS TEST PROGRESS MONITOR"
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
tail -50 "$OUTPUT_FILE" | grep -E "Variation|PHASE|Complete|Success|Error|✅|❌" || echo "No progress markers found yet"

echo ""
echo "------------------------------------------"
echo "Full output file: $OUTPUT_FILE"
echo ""
echo "Run this script again to check progress:"
echo "  bash check_progress.sh"
echo ""
echo "Or view full output:"
echo "  tail -f $OUTPUT_FILE"
