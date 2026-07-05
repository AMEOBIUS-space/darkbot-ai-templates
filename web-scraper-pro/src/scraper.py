"""Web Scraper Pro — advanced scraping with rate limiting, proxy rotation, and export."""
import time
import json
import csv
import random
import urllib.request
import urllib.parse
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import re


@dataclass
class ScrapeResult:
    url: str
    status: int
    content: str
    title: str
    links: List[str]
    emails: List[str]
    phones: List[str]
    scraped_at: str
    error: Optional[str] = None


class RateLimiter:
    """Token bucket rate limiter for polite scraping."""

    def __init__(self, requests_per_second: float = 1.0):
        self.rps = requests_per_second
        self.last_request = 0.0

    def wait(self):
        elapsed = time.time() - self.last_request
        min_interval = 1.0 / self.rps
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        self.last_request = time.time()


class ProxyRotation:
    """Round-robin proxy rotation with failure tracking."""

    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.index = 0
        self.failures = {}

    def next(self) -> Optional[str]:
        if not self.proxies:
            return None
        proxy = self.proxies[self.index % len(self.proxies)]
        self.index += 1
        return proxy

    def mark_failed(self, proxy: str):
        self.failures[proxy] = self.failures.get(proxy, 0) + 1

    def healthy_proxies(self) -> List[str]:
        return [p for p in self.proxies if self.failures.get(p, 0) < 3]


class WebScraperPro:
    """Advanced web scraper with rate limiting, proxy rotation, and data extraction."""

    def __init__(self, rate_limit: float = 1.0, proxies: List[str] = None,
                 user_agents: List[str] = None, timeout: int = 30):
        self.rate_limiter = RateLimiter(rate_limit)
        self.proxy_rotation = ProxyRotation(proxies)
        self.timeout = timeout
        self.user_agents = user_agents or [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        ]
        self.results: List[ScrapeResult] = []

    def _build_request(self, url: str) -> urllib.request.Request:
        proxy = self.proxy_rotation.next()
        headers = {"User-Agent": random.choice(self.user_agents)}
        req = urllib.request.Request(url, headers=headers)
        if proxy:
            handler = urllib.request.ProxyHandler({"http": proxy, "https": proxy})
            opener = urllib.request.build_opener(handler)
            return req, opener
        return req, urllib.request.build_opener()

    def scrape(self, url: str) -> ScrapeResult:
        """Scrape a single URL and extract data."""
        self.rate_limiter.wait()
        try:
            req, opener = self._build_request(url)
            resp = opener.open(req, timeout=self.timeout)
            content = resp.read().decode("utf-8", errors="replace")
            status = resp.getcode()
            return self._extract(url, status, content)
        except urllib.error.HTTPError as e:
            return ScrapeResult(url, e.code, "", "", [], [], [],
                                datetime.now().isoformat(), error=str(e))
        except Exception as e:
            return ScrapeResult(url, 0, "", "", [], [], [],
                                datetime.now().isoformat(), error=str(e))

    def scrape_batch(self, urls: List[str]) -> List[ScrapeResult]:
        """Scrape multiple URLs with rate limiting."""
        results = []
        for url in urls:
            result = self.scrape(url)
            results.append(result)
            self.results.append(result)
        return results

    def _extract(self, url: str, status: int, content: str) -> ScrapeResult:
        """Extract title, links, emails, phones from HTML."""
        title = self._extract_title(content)
        links = self._extract_links(url, content)
        emails = self._extract_emails(content)
        phones = self._extract_phones(content)
        return ScrapeResult(url, status, content[:5000], title, links[:50],
                            emails[:20], phones[:10], datetime.now().isoformat())

    @staticmethod
    def _extract_title(html: str) -> str:
        match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_links(base_url: str, html: str) -> List[str]:
        links = re.findall(r'href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        absolute = []
        for link in links:
            if link.startswith("http"):
                absolute.append(link)
            elif link.startswith("/"):
                parsed = urllib.parse.urlparse(base_url)
                absolute.append(f"{parsed.scheme}://{parsed.netloc}{link}")
        return list(set(absolute))

    @staticmethod
    def _extract_emails(html: str) -> List[str]:
        return list(set(re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)))

    @staticmethod
    def _extract_phones(html: str) -> List[str]:
        return list(set(re.findall(r"\+?\d{1,3}[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}", html)))

    def export_json(self, filepath: str):
        """Export results to JSON file."""
        with open(filepath, "w") as f:
            json.dump([asdict(r) for r in self.results], f, indent=2)

    def export_csv(self, filepath: str):
        """Export results to CSV file."""
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["url", "status", "title", "emails", "phones", "scraped_at", "error"])
            for r in self.results:
                writer.writerow([r.url, r.status, r.title, ";".join(r.emails),
                                 ";".join(r.phones), r.scraped_at, r.error or ""])

    def stats(self) -> Dict:
        """Get scraping statistics."""
        total = len(self.results)
        success = sum(1 for r in self.results if r.status == 200)
        return {
            "total": total,
            "success": success,
            "failed": total - success,
            "success_rate": f"{success / total * 100:.1f}%" if total else "0%",
        }
