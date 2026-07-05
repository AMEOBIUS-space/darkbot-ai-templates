#!/usr/bin/env python3
"""Demo for Email Scraper Template — simulates crawling and email extraction."""
import re, json

def demo():
    print("=" * 50)
    print("📧 DarkBot AI — Email Scraper Demo")
    print("=" * 50)
    print()
    
    # Mock HTML pages
    pages = {
        "https://example.com": '<html><body>Contact: info@example.com, sales@example.com</body></html>',
        "https://example.com/about": '<html><body>CEO: ceo@example.com | Support: support@example.com</body></html>',
        "https://example.com/contact": '<html><body>Email us: hello@example.com</body></html>',
    }
    
    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    
    all_emails = {}
    for url, html in pages.items():
        print(f"📡 Crawling [{1}] {url}")
        found = EMAIL_REGEX.findall(html)
        for email in found:
            email = email.lower()
            if email not in all_emails:
                all_emails[email] = url
                print(f"  ✅ Found: {email}")
    
    print()
    print(f"📊 Results: {len(all_emails)} unique emails")
    print()
    
    # Validate
    print("🔍 Validating:")
    for email in all_emails:
        domain = email.split('@')[1]
        valid = '.' in domain and len(domain) > 3
        print(f"  {'✅' if valid else '❌'} {email} ({'valid' if valid else 'invalid'})")
    
    print()
    print("📤 Export:")
    print(f"  → JSON: emails.json ({len(all_emails)} entries)")
    print(f"  → CSV: emails.csv ({len(all_emails)} rows)")
    print()
    
    print("✅ Features: recursive crawl, dedup, validate, export (JSON/CSV)")
    print("Buy template: @darkbot_ai_bot | $39 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
