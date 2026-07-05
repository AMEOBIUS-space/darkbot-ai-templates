# Content Generator

> SEO meta tags, sitemaps, robots.txt, structured data (JSON-LD), and RSS feeds

## Features

- **MetaTagGenerator** — basic, Open Graph, Twitter Card, full head
- **SitemapGenerator** — XML sitemap with lastmod, changefreq, priority
- **RobotsGenerator** — robots.txt with allow/disallow + sitemap
- **StructuredDataGenerator** — JSON-LD for Article, Product, Breadcrumb
- **RSSGenerator** — RSS 2.0 feed XML
- **ContentGenerator** — facade: article page, sitemap, robots, RSS

## Quick Start

```python
from generator import ContentGenerator, Article

cg = ContentGenerator(site_url="https://example.com", site_name="My Site")

article = Article(title="Hello World", slug="hello-world",
                  content="<p>Content here</p>", description="My first post",
                  keywords=["hello", "world"], author="John")

html = cg.generate_article_page(article)  # Full SEO HTML page
sitemap = cg.generate_sitemap([{"loc": "https://example.com/hello-world"}])
robots = cg.generate_robots(disallow=["/admin"])
rss = cg.generate_rss([article])
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
