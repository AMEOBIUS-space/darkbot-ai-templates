# Web Scraper Pro

> Advanced web scraper with rate limiting, proxy rotation, data extraction, and export

## Features

- Rate limiting (token bucket)
- Proxy rotation with failure tracking
- User-agent rotation
- Title, links, emails, phones extraction
- JSON and CSV export
- Batch scraping
- Statistics reporting

## Quick Start

```python
from scraper import WebScraperPro

scraper = WebScraperPro(rate_limit=2.0, proxies=["proxy1:8080"])
result = scraper.scrape("https://example.com")
print(result.title, result.emails)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
