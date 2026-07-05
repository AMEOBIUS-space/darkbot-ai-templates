# Pagination Helper

> Offset, cursor, keyset, and infinite scroll pagination for any data source

## Features

- **OffsetPaginator** — traditional page/per_page with has_next/has_prev
- **CursorPaginator** — base64-encoded cursors for stateless pagination
- **KeysetPaginator** — sort field-based pagination (efficient for large datasets)
- **InfiniteScroll** — load_more() helper for frontend infinite scroll
- **paginate_response** — JSON API response formatter with URLs

## Quick Start

```python
from pagination import OffsetPaginator, CursorPaginator

# Offset pagination
p = OffsetPaginator(items, per_page=20)
page = p.get_page(1)

# Cursor pagination
cp = CursorPaginator(items, per_page=20)
page = cp.get_page()
next_page = cp.get_page(cursor=page.next_cursor)
```

## Tests

```bash
python -m pytest tests/ -v
```

## License

MIT
