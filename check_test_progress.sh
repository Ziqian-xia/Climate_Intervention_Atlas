#!/bin/bash
# 检查测试进度

echo "=========================================="
echo "Test Progress Check"
echo "=========================================="
echo ""

# 显示最后20行日志
echo "Last 20 lines of output:"
echo "----------------------------------------"
tail -20 two_topics_test_output.log 2>/dev/null || echo "Log file not created yet..."

echo ""
echo "=========================================="
echo "Generated variation directories:"
ls -la test_variations_* 2>/dev/null | head -10 || echo "No output directories yet..."

echo ""
echo "=========================================="
echo "To view full log: tail -f two_topics_test_output.log"
echo "=========================================="
