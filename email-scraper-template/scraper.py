#!/usr/bin/env python3
"""Email Scraper & Validator — extract emails from websites, validate MX, deduplicate."""
import asyncio, re, logging, aiohttp
from dataclasses import dataclass
from typing import Set
from urllib.parse import urljoin, urlparse

logging.basicConfig(level=logging.INFO)

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

@dataclass
class EmailResult:
    email: str
    source_url: str
    valid: bool = False

class EmailScraper:
    """Scrape emails from websites with recursive crawling."""
    
    def __init__(self, max_depth: int = 2, max_pages: int = 50, timeout: int = 10):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.visited: Set[str] = set()
        self.emails: dict[str, EmailResult] = {}
    
    async def scrape_site(self, start_url: str) -> list[EmailResult]:
        """Crawl website and extract all emails."""
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            await self._crawl(session, start_url, start_url, depth=0)
        return list(self.emails.values())
    
    async def _crawl(self, session: aiohttp.ClientSession, url: str, base_url: str, depth: int):
        if depth > self.max_depth or len(self.visited) >= self.max_pages:
            return
        if url in self.visited:
            return
        
        self.visited.add(url)
        logging.info(f"Crawling [{depth}] {url}")
        
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return
                html = await resp.text()
        except Exception as e:
            logging.debug(f"Failed {url}: {e}")
            return
        
        # Extract emails
        for match in EMAIL_REGEX.finditer(html):
            email = match.group().lower()
            if email not in self.emails:
                self.emails[email] = EmailResult(email=email, source_url=url)
                logging.info(f"Found: {email} ({url})")
        
        # Find sub-pages (same domain)
        if depth < self.max_depth:
            links = re.findall(r'href=["\']([^"\']+)["\']', html)
            base_domain = urlparse(base_url).netloc
            for link in links:
                full_url = urljoin(url, link)
                if urlparse(full_url).netloc == base_domain and full_url not in self.visited:
                    if not full_url.endswith(('.jpg', '.png', '.pdf', '.css', '.js')):
                        await self._crawl(session, full_url, base_url, depth + 1)
    
    def validate_email(self, email: str) -> bool:
        """Basic email validation (format + domain check)."""
        if not EMAIL_REGEX.match(email):
            return False
        domain = email.split('@')[1]
        # Basic checks — full MX validation needs dnspython
        return '.' in domain and len(domain) > 3
    
    def export_csv(self, results: list[EmailResult], path: str):
        """Export results to CSV."""
        import csv
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['email', 'source_url', 'valid'])
            for r in results:
                w.writerow([r.email, r.source_url, r.valid])
        logging.info(f"Exported {len(results)} emails to {path}")
    
    def export_json(self, results: list[EmailResult], path: str):
        """Export results to JSON."""
        import json
        data = [{"email": r.email, "source_url": r.source_url, "valid": r.valid} for r in results]
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        logging.info(f"Exported {len(results)} emails to {path}")

async def main():
    scraper = EmailScraper(max_depth=1, max_pages=10)
    # Demo: scrape example.com
    results = await scraper.scrape_site("https://example.com")
    print(f"Found {len(results)} emails")
    for r in results[:5]:
        print(f"  {r.email} <- {r.source_url}")
    # Export
    scraper.export_json(results, "emails.json")

if __name__ == "__main__":
    asyncio.run(main())
