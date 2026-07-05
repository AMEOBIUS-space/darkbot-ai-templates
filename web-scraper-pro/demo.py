#!/usr/bin/env python3
"""Demo: Web Scraper Pro — show extraction on a local HTML string."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from scraper import WebScraperPro

html = """
<html><head><title>Contact Us</title></head>
<body>
  <a href="https://example.com/about">About</a>
  <a href="/products">Products</a>
  <p>Email: info@example.com</p>
  <p>Phone: +1 (555) 123-4567</p>
</body></html>
"""

scraper = WebScraperPro(rate_limit=2.0, proxies=["proxy1:8080", "proxy2:8080"])
result = scraper._extract("https://example.com", 200, html)

print(f"Title: {result.title}")
print(f"Links: {result.links}")
print(f"Emails: {result.emails}")
print(f"Phones: {result.phones}")
print(f"Stats: {scraper.stats()}")
