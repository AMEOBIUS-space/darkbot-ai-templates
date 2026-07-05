"""Pagination Helper — cursor, offset, and keyset pagination for any data source."""
import json
import base64
import hashlib
from typing import Dict, List, Optional, Any, Tuple, Callable, TypeVar, Generic
from dataclasses import dataclass, asdict, field

T = TypeVar('T')


@dataclass
class Page:
    items: List[Any]
    page: int
    per_page: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None


class OffsetPaginator(Generic[T]):
    """Traditional offset-based pagination."""

    def __init__(self, items: List[T], per_page: int = 20):
        self.items = items
        self.per_page = per_page
        self.total = len(items)

    def get_page(self, page: int) -> Page:
        page = max(1, page)
        total_pages = max(1, (self.total + self.per_page - 1) // self.per_page)
        page = min(page, total_pages)

        start = (page - 1) * self.per_page
        end = start + self.per_page
        page_items = self.items[start:end]

        return Page(
            items=page_items,
            page=page,
            per_page=self.per_page,
            total=self.total,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

    def get_all_pages(self) -> List[Page]:
        total_pages = max(1, (self.total + self.per_page - 1) // self.per_page)
        return [self.get_page(p) for p in range(1, total_pages + 1)]


class CursorPaginator(Generic[T]):
    """Cursor-based pagination (base64-encoded position)."""

    def __init__(self, items: List[T], per_page: int = 20,
                 sort_key: str = "id", sort_order: str = "asc"):
        self.items = items
        self.per_page = per_page
        self.sort_key = sort_key
        self.sort_order = sort_order

    def _encode_cursor(self, position: int) -> str:
        data = f"{position}:{self.sort_key}:{self.sort_order}"
        return base64.urlsafe_b64encode(data.encode()).decode()

    def _decode_cursor(self, cursor: str) -> int:
        data = base64.urlsafe_b64decode(cursor.encode()).decode()
        parts = data.split(":")
        return int(parts[0])

    def get_page(self, cursor: str = None) -> Page:
        start = 0
        if cursor:
            start = self._decode_cursor(cursor)

        end = start + self.per_page
        page_items = self.items[start:end]
        total = len(self.items)
        total_pages = max(1, (total + self.per_page - 1) // self.per_page)

        next_cursor = self._encode_cursor(end) if end < total else None
        prev_cursor = self._encode_cursor(max(0, start - self.per_page)) if start > 0 else None

        current_page = start // self.per_page + 1

        return Page(
            items=page_items,
            page=current_page,
            per_page=self.per_page,
            total=total,
            total_pages=total_pages,
            has_next=end < total,
            has_prev=start > 0,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
        )


class KeysetPaginator(Generic[T]):
    """Keyset pagination using a sort field value as cursor."""

    def __init__(self, items: List[T], per_page: int = 20,
                 key_field: str = "id"):
        self.items = sorted(items, key=lambda x: x.get(key_field, 0) if isinstance(x, dict) else getattr(x, key_field, 0))
        self.per_page = per_page
        self.key_field = key_field

    def get_page(self, last_key: Any = None) -> Tuple[List[T], Optional[Any], bool]:
        """Returns (items, next_key, has_next)."""
        start = 0
        if last_key is not None:
            for i, item in enumerate(self.items):
                val = item.get(self.key_field) if isinstance(item, dict) else getattr(item, self.key_field, 0)
                if val > last_key:
                    start = i
                    break
            else:
                return [], None, False

        end = start + self.per_page
        page_items = self.items[start:end]
        has_next = end < len(self.items)

        next_key = None
        if page_items and has_next:
            last_item = page_items[-1]
            next_key = last_item.get(self.key_field) if isinstance(last_item, dict) else getattr(last_item, self.key_field, 0)

        return page_items, next_key, has_next


class InfiniteScroll(Generic[T]):
    """Infinite scroll helper for frontend pagination."""

    def __init__(self, items: List[T], page_size: int = 10):
        self.items = items
        self.page_size = page_size
        self._loaded = 0

    def load_more(self) -> Tuple[List[T], bool]:
        """Load next batch. Returns (items, has_more)."""
        start = self._loaded
        end = start + self.page_size
        batch = self.items[start:end]
        self._loaded = end
        has_more = end < len(self.items)
        return batch, has_more

    def reset(self):
        self._loaded = 0

    @property
    def loaded_count(self) -> int:
        return min(self._loaded, len(self.items))


def paginate_response(page: Page, base_url: str = "") -> Dict:
    """Format a Page as a JSON API response."""
    response = {
        "data": page.items,
        "pagination": {
            "page": page.page,
            "per_page": page.per_page,
            "total": page.total,
            "total_pages": page.total_pages,
            "has_next": page.has_next,
            "has_prev": page.has_prev,
        }
    }
    if page.next_cursor:
        response["pagination"]["next_cursor"] = page.next_cursor
    if page.prev_cursor:
        response["pagination"]["prev_cursor"] = page.prev_cursor
    if base_url:
        response["pagination"]["next_url"] = f"{base_url}?cursor={page.next_cursor}" if page.next_cursor else None
        response["pagination"]["prev_url"] = f"{base_url}?cursor={page.prev_cursor}" if page.prev_cursor else None
    return response
