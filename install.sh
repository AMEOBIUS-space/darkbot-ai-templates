#!/usr/bin/env bash
# DarkBot AI Templates — Quick Installer
# Usage: curl -sL https://raw.githubusercontent.com/AMEOBIUS/darkbot-ai-templates/main/install.sh | bash

set -e

REPO="https://github.com/AMEOBIUS/darkbot-ai-templates.git"
DIR="darkbot-ai-templates"

echo "🤖 DarkBot AI — 18 Production-Ready Code Templates"
echo ""

# Clone
if [ -d "$DIR" ]; then
    echo "📁 $DIR already exists. Updating..."
    cd "$DIR" && git pull --quiet
else
    echo "📥 Cloning..."
    git clone --quiet "$REPO" "$DIR"
    cd "$DIR"
fi

# Count templates
TEMPLATES=$(find . -maxdepth 1 -type d ! -name '.' ! -name 'docs' ! -name '.github' | wc -l)
DEMOS=$(find . -maxdepth 2 -name "demo.py" | wc -l)
TESTS=$(find . -path '*/tests/test_*.py' | wc -l)

echo ""
echo "✅ Installed: $TEMPLATES templates, $DEMOS demos, $TESTS test suites"
echo ""
echo "🎮 Try a demo (no API keys needed):"
echo "   python tg-bot-template/demo.py"
echo "   python crypto-trading-bot/demo.py"
echo "   python web-scraper-template/demo.py"
echo ""
echo "🔧 Or use Make:"
echo "   cd tg-bot-template && make demo"
echo ""
echo "🐳 Docker:"
echo "   cd tg-bot-template && docker-compose up -d"
echo ""
echo "📦 Bundle: \$199 (all 18 + 2h customization)"
echo "💬 Order: @darkbot_ai_bot | BTC/USDT/ETH/XMR"
echo ""
echo "⭐ Star: https://github.com/AMEOBIUS/darkbot-ai-templates"
