#!/bin/bash
# Render the Quarto Markdown report to HTML

echo "=========================================="
echo "Rendering Robustness Analysis Report"
echo "=========================================="
echo ""

REPORT_FILE="Robustness_Analysis_Report.qmd"
OUTPUT_HTML="Robustness_Analysis_Report.html"

# Check if Quarto is installed
if ! command -v quarto &> /dev/null; then
    echo "⚠️  Quarto not found!"
    echo ""
    echo "Option 1: Install Quarto"
    echo "  Download from: https://quarto.org/docs/get-started/"
    echo ""
    echo "Option 2: Use RStudio (includes Quarto)"
    echo "  Open $REPORT_FILE in RStudio and click 'Render'"
    echo ""
    echo "Option 3: Use the standalone HTML version"
    echo "  bash create_standalone_html.sh"
    echo ""
    exit 1
fi

echo "✅ Quarto found: $(quarto --version)"
echo ""

# Render the report
echo "📄 Rendering $REPORT_FILE..."
quarto render "$REPORT_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Report rendered successfully!"
    echo "=========================================="
    echo ""
    echo "📄 Output file: $OUTPUT_HTML"
    echo ""
    echo "To view:"
    echo "  open $OUTPUT_HTML"
    echo ""
else
    echo ""
    echo "❌ Rendering failed. Check the error messages above."
    exit 1
fi
