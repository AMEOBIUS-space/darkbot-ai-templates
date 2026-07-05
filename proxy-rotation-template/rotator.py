#!/usr/bin/env python3
"""Proxy Rotation Manager — pool management, health checks, auto-rotation."""
import asyncio, random, time, logging, aiohttp
from dataclasses import dataclass, field
from typing import Optional

logging.basicConfig(level=logging.INFO)

@dataclass
class Proxy:
    host: str
    port: int
    username: str = ""
    password: str = ""
    protocol: str = "http"  # http, socks5, socks4
    healthy: bool = True
    last_check: float = 0
    fail_count: int = 0
    latency_ms: int = 0
    
    @property
    def url(self) -> str:
        auth = f"{self.username}:{self.password}@" if self.username else ""
        return f"{self.protocol}://{auth}{self.host}:{self.port}"

class ProxyRotator:
    """Rotate proxies with health checking and failover."""
    
    def __init__(self, proxies: list[Proxy], max_fails: int = 3, check_url: str = "https://httpbin.org/ip"):
        self.proxies = proxies
        self.max_fails = max_fails
        self.check_url = check_url
        self._idx = 0
    
    def get_next(self) -> Optional[Proxy]:
        """Get next healthy proxy (round-robin)."""
        healthy = [p for p in self.proxies if p.healthy]
        if not healthy:
            return None
        proxy = healthy[self._idx % len(healthy)]
        self._idx += 1
        return proxy
    
    def get_random(self) -> Optional[Proxy]:
        """Get random healthy proxy."""
        healthy = [p for p in self.proxies if p.healthy]
        return random.choice(healthy) if healthy else None
    
    def mark_failed(self, proxy: Proxy):
        """Mark proxy as failed, disable if too many fails."""
        proxy.fail_count += 1
        if proxy.fail_count >= self.max_fails:
            proxy.healthy = False
            logging.warning(f"Proxy {proxy.host}:{proxy.port} disabled ({proxy.fail_count} fails)")
    
    def mark_healthy(self, proxy: Proxy, latency_ms: int):
        """Mark proxy as healthy with latency."""
        proxy.healthy = True
        proxy.fail_count = 0
        proxy.latency_ms = latency_ms
        proxy.last_check = time.time()
    
    async def health_check(self, proxy: Proxy) -> bool:
        """Check proxy health."""
        try:
            start = time.time()
            async with aiohttp.ClientSession() as session:
                connector = aiohttp.ProxyConnector.from_url(proxy.url) if proxy.protocol != "http" else None
                async with session.get(self.check_url, proxy=proxy.url if proxy.protocol == "http" else None, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        self.mark_healthy(proxy, int((time.time() - start) * 1000))
                        return True
        except Exception:
            self.mark_failed(proxy)
        return False
    
    async def check_all(self):
        """Health check all proxies concurrently."""
        tasks = [self.health_check(p) for p in self.proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        healthy = sum(1 for p in self.proxies if p.healthy)
        logging.info(f"Health check: {healthy}/{len(self.proxies)} healthy")
    
    def stats(self) -> dict:
        """Get proxy pool statistics."""
        return {
            "total": len(self.proxies),
            "healthy": sum(1 for p in self.proxies if p.healthy),
            "unhealthy": sum(1 for p in self.proxies if not p.healthy),
            "avg_latency": sum(p.latency_ms for p in self.proxies if p.healthy) / max(1, sum(1 for p in self.proxies if p.healthy)),
        }

def load_proxies_from_file(path: str) -> list[Proxy]:
    """Load proxies from file (format: protocol://user:pass@host:port per line)."""
    proxies = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Parse protocol://user:pass@host:port
            protocol = "http"
            if "://" in line:
                protocol, rest = line.split("://", 1)
            else:
                rest = line
            auth = ""
            if "@" in rest:
                auth, rest = rest.rsplit("@", 1)
            host, port = rest.split(":")
            username, password = ("", "")
            if auth and ":" in auth:
                username, password = auth.split(":", 1)
            proxies.append(Proxy(host=host, port=int(port), username=username, password=password, protocol=protocol))
    return proxies

if __name__ == "__main__":
    # Demo with sample proxies
    proxies = [
        Proxy("127.0.0.1", 8080, protocol="http"),
        Proxy("127.0.0.1", 1080, protocol="socks5"),
    ]
    rotator = ProxyRotator(proxies)
    print(f"Stats: {rotator.stats()}")
    print(f"Next proxy: {rotator.get_next().url}")
    print(f"Random proxy: {rotator.get_random().url}")
