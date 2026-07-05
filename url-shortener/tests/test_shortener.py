import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from shortener import URLShortener, encode_base62, decode_base62


def test_encode_base62():
    assert encode_base62(0) == "0"
    assert encode_base62(10) == "A"
    assert encode_base62(61) == "z"
    assert encode_base62(62) == "10"

def test_decode_base62():
    assert decode_base62("0") == 0
    assert decode_base62("A") == 10
    assert decode_base62("z") == 61
    assert decode_base62("10") == 62

def test_encode_decode_roundtrip():
    for num in [0, 1, 100, 9999, 100000, 9999999]:
        assert decode_base62(encode_base62(num)) == num

def test_shorten_basic():
    us = URLShortener()
    code = us.shorten("https://example.com/very/long/url")
    assert len(code) >= 6
    assert code in us._urls

def test_resolve():
    us = URLShortener()
    code = us.shorten("https://example.com")
    assert us.resolve(code) == "https://example.com"

def test_resolve_nonexistent():
    us = URLShortener()
    assert us.resolve("nonexistent") is None

def test_click_tracking():
    us = URLShortener()
    code = us.shorten("https://example.com")
    us.resolve(code)
    us.resolve(code)
    us.resolve(code)
    assert us._urls[code].clicks == 3

def test_custom_alias():
    us = URLShortener()
    code = us.shorten("https://example.com", custom_alias="mylink")
    assert code == "mylink"
    assert us.resolve("mylink") == "https://example.com"

def test_custom_alias_taken():
    us = URLShortener()
    us.shorten("https://a.com", custom_alias="taken")
    try:
        us.shorten("https://b.com", custom_alias="taken")
        assert False
    except ValueError:
        pass

def test_duplicate_url():
    us = URLShortener()
    code1 = us.shorten("https://example.com")
    code2 = us.shorten("https://example.com")
    assert code1 == code2  # Same URL gets same code

def test_password_protection():
    us = URLShortener()
    code = us.shorten("https://secret.com", password="pass123")
    assert us.resolve(code) is None  # No password
    assert us.resolve(code, password="wrong") is None  # Wrong password
    assert us.resolve(code, password="pass123") == "https://secret.com"  # Correct

def test_expiration():
    us = URLShortener()
    code = us.shorten("https://temp.com", expires_days=-1)  # Already expired
    assert us.resolve(code) is None

def test_delete():
    us = URLShortener()
    code = us.shorten("https://example.com")
    assert us.delete(code) is True
    assert us.resolve(code) is None
    assert us.delete("nonexistent") is False

def test_get_info():
    us = URLShortener()
    code = us.shorten("https://example.com", custom_alias="info")
    info = us.get_info("info")
    assert info["original_url"] == "https://example.com"
    assert info["clicks"] == 0
    assert info["custom_alias"] is True

def test_top_urls():
    us = URLShortener()
    c1 = us.shorten("https://a.com")
    c2 = us.shorten("https://b.com")
    for _ in range(10):
        us.resolve(c1)
    for _ in range(5):
        us.resolve(c2)
    top = us.top_urls(2)
    assert top[0]["clicks"] == 10
    assert top[1]["clicks"] == 5

def test_qrcode_url():
    us = URLShortener()
    code = us.shorten("https://example.com")
    qr = us.qrcode_url(code)
    assert "chart.googleapis.com" in qr
    assert "qr" in qr

def test_qrcode_nonexistent():
    us = URLShortener()
    assert us.qrcode_url("nonexistent") is None

def test_cleanup_expired():
    us = URLShortener()
    us.shorten("https://temp.com", expires_days=-1)
    us.shorten("https://perm.com")
    removed = us.cleanup_expired()
    assert removed == 1

def test_stats():
    us = URLShortener()
    us.shorten("https://a.com")
    us.shorten("https://b.com", custom_alias="b", password="x")
    us.resolve("b", password="x")
    stats = us.stats()
    assert stats["total_urls"] == 2
    assert stats["total_clicks"] == 1
    assert stats["custom_aliases"] == 1
    assert stats["password_protected"] == 1

def test_list_urls():
    us = URLShortener()
    us.shorten("https://a.com")
    us.shorten("https://b.com")
    urls = us.list_urls()
    assert len(urls) == 2
