import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from scraper import WebScraperPro, RateLimiter, ProxyRotation, ScrapeResult


def test_rate_limiter():
    rl = RateLimiter(10.0)
    import time
    start = time.time()
    rl.wait()
    rl.wait()
    elapsed = time.time() - start
    assert elapsed < 1.0


def test_proxy_rotation():
    pr = ProxyRotation(["proxy1", "proxy2", "proxy3"])
    assert pr.next() == "proxy1"
    assert pr.next() == "proxy2"
    assert pr.next() == "proxy3"
    assert pr.next() == "proxy1"


def test_proxy_healthy():
    pr = ProxyRotation(["p1", "p2"])
    pr.mark_failed("p1")
    pr.mark_failed("p1")
    pr.mark_failed("p1")
    assert "p1" not in pr.healthy_proxies()
    assert "p2" in pr.healthy_proxies()


def test_extract_title():
    html = "<html><head><title>Test Page</title></head></html>"
    assert WebScraperPro._extract_title(html) == "Test Page"


def test_extract_title_empty():
    assert WebScraperPro._extract_title("<html></html>") == ""


def test_extract_emails():
    html = "Contact: john@example.com and jane@test.org"
    emails = WebScraperPro._extract_emails(html)
    assert "john@example.com" in emails
    assert "jane@test.org" in emails


def test_extract_phones():
    html = "Call: +1 (555) 123-4567 or 555-987-6543"
    phones = WebScraperPro._extract_phones(html)
    assert len(phones) >= 1


def test_extract_links():
    html = '<a href="https://example.com/page">link</a><a href="/relative">rel</a>'
    links = WebScraperPro._extract_links("https://example.com", html)
    assert "https://example.com/page" in links
    assert "https://example.com/relative" in links


def test_scraper_init():
    scraper = WebScraperPro(rate_limit=2.0, proxies=["p1", "p2"])
    assert scraper.rate_limiter.rps == 2.0
    assert len(scraper.proxy_rotation.proxies) == 2
    assert len(scraper.user_agents) == 3


def test_stats_empty():
    scraper = WebScraperPro()
    assert scraper.stats()["total"] == 0


def test_export_json(tmp_path):
    scraper = WebScraperPro()
    scraper.results.append(ScrapeResult("https://test.com", 200, "content", "Test", [], [], [], "2026-01-01"))
    filepath = str(tmp_path / "results.json")
    scraper.export_json(filepath)
    import json
    data = json.load(open(filepath))
    assert len(data) == 1
    assert data[0]["url"] == "https://test.com"


def test_export_csv(tmp_path):
    scraper = WebScraperPro()
    scraper.results.append(ScrapeResult("https://test.com", 200, "content", "Test", ["a@b.com"], [], [], "2026-01-01"))
    filepath = str(tmp_path / "results.csv")
    scraper.export_csv(filepath)
    import csv
    with open(filepath) as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert rows[0][0] == "url"
        assert rows[1][0] == "https://test.com"
