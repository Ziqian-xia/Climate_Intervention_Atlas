#!/bin/bash
# Playwright Installation Script for Full-Text Retrieval

echo "================================================================================"
echo "Playwright Installation for Full-Text Retrieval"
echo "================================================================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated"
    echo "   Attempting to activate .venv..."
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ .venv not found. Please create it first:"
        echo "   python3 -m venv .venv"
        echo "   source .venv/bin/activate"
        exit 1
    fi
fi

echo ""
echo "Step 1: Installing Playwright Python package..."
echo "--------------------------------------------------------------------------------"
pip install playwright>=1.43.0

if [ $? -ne 0 ]; then
    echo "❌ Failed to install Playwright package"
    exit 1
fi

echo ""
echo "✅ Playwright package installed"
echo ""

echo "Step 2: Downloading Chromium browser..."
echo "--------------------------------------------------------------------------------"
python3 -m playwright install chromium

if [ $? -ne 0 ]; then
    echo "❌ Failed to download Chromium"
    exit 1
fi

echo ""
echo "✅ Chromium browser downloaded"
echo ""

echo "Step 3: Verifying installation..."
echo "--------------------------------------------------------------------------------"
python3 -c "from playwright.sync_api import sync_playwright; print('✅ Playwright import successful')"

if [ $? -ne 0 ]; then
    echo "❌ Playwright verification failed"
    exit 1
fi

echo ""
echo "Step 4: Testing basic functionality..."
echo "--------------------------------------------------------------------------------"
python3 << 'EOF'
from playwright.sync_api import sync_playwright

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://example.com", timeout=10000)
        title = page.title()
        browser.close()
        print(f"✅ Browser test successful: {title}")
except Exception as e:
    print(f"❌ Browser test failed: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo "❌ Browser test failed"
    exit 1
fi

echo ""
echo "================================================================================"
echo "🎉 Playwright Installation Complete!"
echo "================================================================================"
echo ""
echo "You can now use Playwright fallback in full-text retrieval:"
echo ""
echo "Option 1: In Streamlit app"
echo "  • Open: http://localhost:8502"
echo "  • Phase 4 → ☑️ Use Playwright Fallback"
echo ""
echo "Option 2: Command line"
echo "  • python3 fulltext_chain_wrapper.py --use-playwright-fallback ..."
echo ""
echo "⚠️  Important Notes:"
echo "  • Playwright is SLOW (30-60s per paper)"
echo "  • Use only as last resort for paywalled content"
echo "  • API methods (Wiley/OpenAlex) are much faster"
echo ""
echo "For detailed usage, see: PLAYWRIGHT_SETUP_GUIDE.md"
echo ""
