"""Content Generator — SEO articles, meta tags, sitemaps, and structured data."""
import json
import html
import re
import hashlib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape


@dataclass
class MetaTag:
    name: str
    content: str
    property: bool = False  # True for og: tags (property=), False for name=


@dataclass
class Article:
    title: str
    slug: str
    content: str
    description: str = ""
    keywords: List[str] = field(default_factory=list)
    author: str = ""
    published_at: str = ""
    tags: List[str] = field(default_factory=list)
    canonical_url: str = ""


class MetaTagGenerator:
    """Generate HTML meta tags for SEO."""

    @staticmethod
    def basic(title: str, description: str, keywords: List[str] = None) -> List[MetaTag]:
        tags = [
            MetaTag(name="title", content=title),
            MetaTag(name="description", content=description),
        ]
        if keywords:
            tags.append(MetaTag(name="keywords", content=", ".join(keywords)))
        return tags

    @staticmethod
    def open_graph(title: str, description: str, url: str, image: str = "",
                   site_name: str = "", type: str = "website") -> List[MetaTag]:
        return [
            MetaTag(name="og:title", content=title, property=True),
            MetaTag(name="og:description", content=description, property=True),
            MetaTag(name="og:url", content=url, property=True),
            MetaTag(name="og:type", content=type, property=True),
            MetaTag(name="og:image", content=image, property=True),
            MetaTag(name="og:site_name", content=site_name, property=True),
        ]

    @staticmethod
    def twitter_card(title: str, description: str, image: str = "",
                     card: str = "summary_large_image") -> List[MetaTag]:
        return [
            MetaTag(name="twitter:card", content=card),
            MetaTag(name="twitter:title", content=title),
            MetaTag(name="twitter:description", content=description),
            MetaTag(name="twitter:image", content=image),
        ]

    @staticmethod
    def render(tags: List[MetaTag]) -> str:
        lines = []
        for tag in tags:
            attr = "property" if tag.property else "name"
            lines.append(f'<meta {attr}="{escape(tag.name)}" content="{escape(tag.content)}" />')
        return "\n".join(lines)

    @staticmethod
    def full_head(title: str, description: str, url: str, keywords: List[str] = None,
                  image: str = "", site_name: str = "") -> str:
        tags = []
        tags.extend(MetaTagGenerator.basic(title, description, keywords))
        tags.extend(MetaTagGenerator.open_graph(title, description, url, image, site_name))
        tags.extend(MetaTagGenerator.twitter_card(title, description, image))
        return MetaTagGenerator.render(tags)


class SitemapGenerator:
    """Generate XML sitemaps."""

    @staticmethod
    def generate(urls: List[Dict], changefreq: str = "weekly",
                 priority: str = "0.8") -> str:
        """Generate sitemap XML. Each url dict: {loc, lastmod?, changefreq?, priority?}"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        for entry in urls:
            lines.append("  <url>")
            lines.append(f"    <loc>{escape(entry['loc'])}</loc>")
            if "lastmod" in entry:
                lines.append(f"    <lastmod>{entry['lastmod']}</lastmod>")
            lines.append(f"    <changefreq>{entry.get('changefreq', changefreq)}</changefreq>")
            lines.append(f"    <priority>{entry.get('priority', priority)}</priority>")
            lines.append("  </url>")
        lines.append("</urlset>")
        return "\n".join(lines)


class RobotsGenerator:
    """Generate robots.txt."""

    @staticmethod
    def generate(allow: List[str] = None, disallow: List[str] = None,
                 sitemap: str = "", user_agent: str = "*") -> str:
        lines = [f"User-agent: {user_agent}"]
        for path in (allow or ["/"]):
            lines.append(f"Allow: {path}")
        for path in (disallow or []):
            lines.append(f"Disallow: {path}")
        if sitemap:
            lines.append(f"\nSitemap: {sitemap}")
        return "\n".join(lines)


class StructuredDataGenerator:
    """Generate JSON-LD structured data."""

    @staticmethod
    def article(title: str, description: str, url: str, image: str = "",
                author: str = "", published: str = "", modified: str = "") -> str:
        data = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "url": url,
        }
        if image:
            data["image"] = image
        if author:
            data["author"] = {"@type": "Person", "name": author}
        if published:
            data["datePublished"] = published
        if modified:
            data["dateModified"] = modified
        return f'<script type="application/ld+json">\n{json.dumps(data, indent=2)}\n</script>'

    @staticmethod
    def product(name: str, description: str, price: float, currency: str = "USD",
                rating: float = 0, reviews: int = 0, image: str = "") -> str:
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": name,
            "description": description,
            "offers": {
                "@type": "Offer",
                "price": str(price),
                "priceCurrency": currency,
                "availability": "https://schema.org/InStock",
            },
        }
        if rating:
            data["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(rating),
                "reviewCount": str(reviews),
            }
        if image:
            data["image"] = image
        return f'<script type="application/ld+json">\n{json.dumps(data, indent=2)}\n</script>'

    @staticmethod
    def breadcrumb(items: List[Dict]) -> str:
        """items: [{name, url}, ...]"""
        elements = []
        for i, item in enumerate(items):
            elements.append({
                "@type": "ListItem",
                "position": i + 1,
                "name": item["name"],
                "item": item["url"],
            })
        data = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": elements,
        }
        return f'<script type="application/ld+json">\n{json.dumps(data, indent=2)}\n</script>'


class RSSGenerator:
    """Generate RSS feeds."""

    @staticmethod
    def generate(channel_title: str, channel_url: str, channel_desc: str,
                 items: List[Dict]) -> str:
        """Generate RSS XML. Each item: {title, link, description, pub_date?, guid?}"""
        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append('<rss version="2.0">')
        lines.append("  <channel>")
        lines.append(f"    <title>{escape(channel_title)}</title>")
        lines.append(f"    <link>{escape(channel_url)}</link>")
        lines.append(f"    <description>{escape(channel_desc)}</description>")
        for item in items:
            lines.append("    <item>")
            lines.append(f"      <title>{escape(item['title'])}</title>")
            lines.append(f"      <link>{escape(item['link'])}</link>")
            lines.append(f"      <description>{escape(item['description'])}</description>")
            if "pub_date" in item:
                lines.append(f"      <pubDate>{item['pub_date']}</pubDate>")
            guid = item.get("guid", item["link"])
            lines.append(f"      <guid>{escape(guid)}</guid>")
            lines.append("    </item>")
        lines.append("  </channel>")
        lines.append("</rss>")
        return "\n".join(lines)


class ContentGenerator:
    """Main content generation facade."""

    def __init__(self, site_url: str = "", site_name: str = ""):
        self.site_url = site_url
        self.site_name = site_name

    def generate_article_page(self, article: Article) -> str:
        """Generate a complete HTML article page with SEO."""
        url = article.canonical_url or f"{self.site_url}/{article.slug}"
        head = MetaTagGenerator.full_head(
            title=article.title,
            description=article.description,
            url=url,
            keywords=article.keywords,
            site_name=self.site_name,
        )
        structured = StructuredDataGenerator.article(
            title=article.title,
            description=article.description,
            url=url,
            author=article.author,
            published=article.published_at,
        )
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
{head}
{structured}
</head>
<body>
<article>
<h1>{escape(article.title)}</h1>
{article.content}
</article>
</body>
</html>"""

    def generate_sitemap(self, pages: List[Dict]) -> str:
        return SitemapGenerator.generate(pages)

    def generate_robots(self, disallow: List[str] = None) -> str:
        return RobotsGenerator.generate(disallow=disallow, sitemap=f"{self.site_url}/sitemap.xml")

    def generate_rss(self, articles: List[Article]) -> str:
        items = [
            {
                "title": a.title,
                "link": f"{self.site_url}/{a.slug}",
                "description": a.description,
                "pub_date": a.published_at,
            }
            for a in articles
        ]
        return RSSGenerator.generate(self.site_name, self.site_url, self.site_name, items)
