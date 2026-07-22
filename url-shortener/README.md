# URL Shortener

> Base62 encoding, custom aliases, click analytics, password protection, and QR codes

## Features

- Base62 encoding/decoding
- Custom aliases (e.g., short.link/mylink)
- Click tracking with history
- Password protection
- URL expiration
- Duplicate URL detection (same URL = same code)
- Top URLs by clicks
- QR code URL generation (Google Charts)
- Expired URL cleanup
- Statistics dashboard

## Quick Start

```python
from shortener import URLShortener

us = URLShortener(base_url="https://my.link")
code = us.shorten("https://example.com/very/long/url", custom_alias="mylink")
url = us.resolve("mylink")  # Returns original URL, increments clicks
qr = us.qrcode_url("mylink")  # QR code URL
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT

Freelance portfolio: [https://ameobius-space.github.io/kwork-portfolio/](https://ameobius-space.github.io/kwork-portfolio/)
