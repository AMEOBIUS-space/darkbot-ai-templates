#!/usr/bin/env python3
"""Tor Market Scraper Template — scrape .onion marketplaces via Tor SOCKS5 proxy.
Anti-detection, rotating circuits, product extraction, price monitoring."""
import asyncio, re, json, logging, time
from typing import List, Optional
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)

@dataclass
class MarketListing:
    title: str
    price: str
    vendor: str
    url: str
    category: str = ""
    ships_from: str = ""
    ships_to: str = ""
    rating: float = 0
    sales: int = 0
    scraped_at: str = ""

class TorMarketScraper:
    """Scrape .onion marketplaces via Tor proxy."""
    
    def __init__(self, tor_proxy: str = "socks5://127.0.0.1:9050", timeout: int = 30):
        self.tor_proxy = tor_proxy
        self.timeout = timeout
    
    async def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch .onion page via Tor with retries."""
        import aiohttp
        from aiohttp_socks import ProxyConnector
        
        for attempt in range(retries):
            try:
                connector = ProxyConnector.from_url(self.tor_proxy)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                        url,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    ) as resp:
                        if resp.status == 200:
                            return await resp.text()
                        logging.warning(f"HTTP {resp.status} on {url}")
            except Exception as e:
                logging.debug(f"Attempt {attempt+1}: {e}")
                await asyncio.sleep(5)
        return None
    
    def extract_listings(self, html: str, base_url: str) -> List[MarketListing]:
        """Extract product listings from marketplace HTML.
        Override this method for specific marketplaces."""
        listings = []
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Generic extraction patterns (adjust per marketplace)
        # Pattern 1: <div class="product"> with title, price
        products = re.findall(r'<div[^>]*class="[^"]*product[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
        for p in products:
            title = re.search(r'<a[^>]*>([^<]+)</a>', p)
            price = re.search(r'(?:price|cost)[^<]*?([\d.]+)\s*(?:USD|EUR|BTC|XMR|\$)', p, re.I)
            if title:
                listings.append(MarketListing(
                    title=title.group(1).strip()[:100],
                    price=price.group(1) if price else "",
                    vendor="",
                    url=base_url,
                    scraped_at=now
                ))
        
        # Pattern 2: JSON-LD structured data
        jsonld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for j in jsonld:
            try:
                data = json.loads(j)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "Product":
                            listings.append(MarketListing(
                                title=item.get("name", "")[:100],
                                price=str(item.get("offers", {}).get("price", "")),
                                vendor=item.get("brand", {}).get("name", ""),
                                url=base_url,
                                scraped_at=now
                            ))
            except json.JSONDecodeError:
                continue
        
        logging.info(f"Extracted {len(listings)} listings from {base_url}")
        return listings
    
    async def scrape_market(self, url: str, max_pages: int = 5) -> List[MarketListing]:
        """Scrape marketplace with pagination support."""
        all_listings = []
        for page in range(1, max_pages + 1):
            page_url = f"{url}?page={page}" if "?" not in url else f"{url}&page={page}"
            html = await self.fetch_page(page_url)
            if not html:
                break
            listings = self.extract_listings(html, url)
            if not listings:
                break
            all_listings.extend(listings)
            await asyncio.sleep(3)  # Rate limit
        return all_listings
    
    async def monitor_prices(self, url: str, check_interval: int = 3600, callback=None):
        """Monitor market prices continuously."""
        while True:
            listings = await self.scrape_market(url)
            if callback and listings:
                await callback(listings) if asyncio.iscoroutinefunction(callback) else callback(listings)
            logging.info(f"Monitoring {url}: {len(listings)} listings. Next check in {check_interval}s")
            await asyncio.sleep(check_interval)
    
    def export_json(self, listings: List[MarketListing], path: str):
        """Export to JSON."""
        data = [{"title": l.title, "price": l.price, "vendor": l.vendor, "url": l.url,
                 "category": l.category, "rating": l.rating, "sales": l.sales, "scraped_at": l.scraped_at}
                for l in listings]
        with open(path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Exported {len(listings)} to {path}")
    
    def export_csv(self, listings: List[MarketListing], path: str):
        """Export to CSV."""
        import csv
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["title", "price", "vendor", "category", "rating", "sales", "url", "scraped_at"])
            for l in listings:
                w.writerow([l.title, l.price, l.vendor, l.category, l.rating, l.sales, l.url, l.scraped_at])
        logging.info(f"Exported CSV to {path}")

async def main():
    scraper = TorMarketScraper(tor_proxy="socks5://127.0.0.1:9050")
    # Demo — replace with actual .onion marketplace URL
    # listings = await scraper.scrape_market("http://example.onion/products")
    # scraper.export_json(listings, "listings.json")
    print("Tor Market Scraper template ready.")
    print("Set tor_proxy and marketplace URL to start scraping.")

if __name__ == "__main__":
    asyncio.run(main())
