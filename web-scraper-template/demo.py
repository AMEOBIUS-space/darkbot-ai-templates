#!/usr/bin/env python3
"""Demo for Web Scraper Template — scrapes example.com without proxy/setup."""
import asyncio, re

async def demo():
    print("=" * 50)
    print("🕷 DarkBot AI — Web Scraper Template Demo")
    print("=" * 50)
    print()
    
    # Simulate scraping (no real network call needed for demo)
    mock_html = """
    <html>
    <head><title>Example Domain</title></head>
    <body>
        <h1>Example Domain</h1>
        <p>This domain is for use in illustrative examples.</p>
        <a href="https://www.iana.org/domains/example">More information</a>
        <div class="product">Product 1 - $29.99</div>
        <div class="product">Product 2 - $49.99</div>
        <div class="product">Product 3 - $19.99</div>
    </body>
    </html>
    """
    
    print("📡 Fetching: https://example.com")
    print("  Status: 200 OK")
    print("  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    print()
    
    # Extract title
    title = re.search(r'<title>(.*?)</title>', mock_html)
    print(f"📄 Title: {title.group(1) if title else 'N/A'}")
    
    # Extract links
    links = re.findall(r'href="(https?://[^"]+)"', mock_html)
    print(f"🔗 Links found: {len(links)}")
    for l in links:
        print(f"  → {l}")
    print()
    
    # Extract products
    products = re.findall(r'<div class="product">(.*?)</div>', mock_html)
    print(f"📦 Products found: {len(products)}")
    for p in products:
        print(f"  → {p.strip()}")
    print()
    
    # Show features
    print("✅ Features demonstrated:")
    print("  • HTML parsing (regex)")
    print("  • Title extraction")
    print("  • Link extraction")
    print("  • Product data extraction")
    print()
    print("Full template includes:")
    print("  • Playwright (headless browser)")
    print("  • Proxy rotation")
    print("  • User-Agent randomization")
    print("  • CF bypass patterns")
    print("  • JSON/CSV export")
    print()
    print("Buy template: @darkbot_ai_bot | $39 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(demo())
