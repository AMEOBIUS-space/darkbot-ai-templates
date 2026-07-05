import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from generator import (MetaTagGenerator, SitemapGenerator, RobotsGenerator,
                       StructuredDataGenerator, RSSGenerator, ContentGenerator, Article)


def test_basic_meta():
    tags = MetaTagGenerator.basic("Test Page", "A test page", ["test", "page"])
    assert len(tags) == 3
    assert tags[0].name == "title"
    assert tags[1].name == "description"


def test_open_graph():
    tags = MetaTagGenerator.open_graph("Title", "Desc", "https://example.com",
                                       image="https://example.com/img.jpg")
    assert any(t.name == "og:title" for t in tags)
    assert any(t.name == "og:image" for t in tags)
    assert all(t.property for t in tags)


def test_twitter_card():
    tags = MetaTagGenerator.twitter_card("Title", "Desc")
    assert any(t.name == "twitter:card" for t in tags)
    assert any(t.name == "twitter:title" for t in tags)


def test_render_meta():
    tags = [MetaTagGenerator.basic("Test", "Desc")[0]]
    html = MetaTagGenerator.render(tags)
    assert '<meta name="title"' in html
    assert 'content="Test"' in html


def test_full_head():
    head = MetaTagGenerator.full_head("Title", "Desc", "https://example.com",
                                      keywords=["a", "b"], image="https://example.com/img.jpg")
    assert "og:title" in head
    assert "twitter:card" in head
    assert "keywords" in head


def test_sitemap():
    urls = [{"loc": "https://example.com/page1"}, {"loc": "https://example.com/page2"}]
    xml = SitemapGenerator.generate(urls)
    assert "<urlset" in xml
    assert "page1" in xml
    assert "page2" in xml


def test_sitemap_with_lastmod():
    urls = [{"loc": "https://example.com", "lastmod": "2026-01-01"}]
    xml = SitemapGenerator.generate(urls)
    assert "<lastmod>2026-01-01</lastmod>" in xml


def test_robots():
    txt = RobotsGenerator.generate(disallow=["/admin"], sitemap="https://example.com/sitemap.xml")
    assert "User-agent: *" in txt
    assert "Disallow: /admin" in txt
    assert "Sitemap:" in txt


def test_structured_article():
    jsonld = StructuredDataGenerator.article("Title", "Desc", "https://example.com/a")
    assert '"@type": "Article"' in jsonld
    assert "Title" in jsonld


def test_structured_product():
    jsonld = StructuredDataGenerator.product("Widget", "A widget", 19.99)
    assert '"@type": "Product"' in jsonld
    assert "19.99" in jsonld


def test_structured_breadcrumb():
    jsonld = StructuredDataGenerator.breadcrumb([
        {"name": "Home", "url": "https://example.com"},
        {"name": "Products", "url": "https://example.com/products"},
    ])
    assert "BreadcrumbList" in jsonld
    assert "Products" in jsonld


def test_rss():
    items = [{"title": "Post 1", "link": "https://example.com/1", "description": "Desc 1"}]
    xml = RSSGenerator.generate("My Blog", "https://example.com", "My blog", items)
    assert "<rss" in xml
    assert "Post 1" in xml
    assert "<item>" in xml


def test_content_generator_article():
    cg = ContentGenerator(site_url="https://example.com", site_name="My Site")
    article = Article(title="Test Article", slug="test-article",
                      content="<p>Hello world</p>", description="A test article",
                      keywords=["test"], author="John")
    html = cg.generate_article_page(article)
    assert "<!DOCTYPE html>" in html
    assert "Test Article" in html
    assert "og:title" in html


def test_content_generator_sitemap():
    cg = ContentGenerator(site_url="https://example.com")
    xml = cg.generate_sitemap([{"loc": "https://example.com/page1"}])
    assert "<urlset" in xml


def test_content_generator_robots():
    cg = ContentGenerator(site_url="https://example.com")
    txt = cg.generate_robots(disallow=["/private"])
    assert "Disallow: /private" in txt
    assert "https://example.com/sitemap.xml" in txt


def test_content_generator_rss():
    cg = ContentGenerator(site_url="https://example.com", site_name="My Site")
    articles = [Article(title="A", slug="a", content="x", description="d", published_at="2026-01-01")]
    xml = cg.generate_rss(articles)
    assert "<rss" in xml
    assert "My Site" in xml
