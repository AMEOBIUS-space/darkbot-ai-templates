import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pagination import OffsetPaginator, CursorPaginator, KeysetPaginator, InfiniteScroll, paginate_response, Page


def test_offset_basic():
    items = list(range(100))
    p = OffsetPaginator(items, per_page=10)
    page = p.get_page(1)
    assert len(page.items) == 10
    assert page.page == 1
    assert page.total == 100
    assert page.total_pages == 10
    assert page.has_next is True
    assert page.has_prev is False


def test_offset_last_page():
    items = list(range(25))
    p = OffsetPaginator(items, per_page=10)
    page = p.get_page(3)
    assert len(page.items) == 5
    assert page.has_next is False
    assert page.has_prev is True


def test_offset_out_of_range():
    items = list(range(10))
    p = OffsetPaginator(items, per_page=5)
    page = p.get_page(999)
    assert page.page == 2  # Clamped to last page


def test_offset_empty():
    p = OffsetPaginator([], per_page=10)
    page = p.get_page(1)
    assert page.total == 0
    assert page.total_pages == 1


def test_cursor_basic():
    items = list(range(50))
    p = CursorPaginator(items, per_page=10)
    page = p.get_page()
    assert len(page.items) == 10
    assert page.has_next is True
    assert page.next_cursor is not None


def test_cursor_next():
    items = list(range(50))
    p = CursorPaginator(items, per_page=10)
    page1 = p.get_page()
    page2 = p.get_page(cursor=page1.next_cursor)
    assert page2.items[0] == 10


def test_cursor_prev():
    items = list(range(50))
    p = CursorPaginator(items, per_page=10)
    page1 = p.get_page()
    page2 = p.get_page(cursor=page1.next_cursor)
    page3 = p.get_page(cursor=page2.prev_cursor)
    assert page3.items[0] == 0


def test_cursor_last():
    items = list(range(10))
    p = CursorPaginator(items, per_page=5)
    page1 = p.get_page()
    page2 = p.get_page(cursor=page1.next_cursor)
    assert page2.has_next is False


def test_keyset_basic():
    items = [{"id": i, "name": f"item_{i}"} for i in range(20)]
    p = KeysetPaginator(items, per_page=5, key_field="id")
    page_items, next_key, has_next = p.get_page()
    assert len(page_items) == 5
    assert has_next is True
    assert next_key == 4


def test_keyset_next():
    items = [{"id": i} for i in range(20)]
    p = KeysetPaginator(items, per_page=5, key_field="id")
    _, next_key, _ = p.get_page()
    page_items, next_key2, has_next = p.get_page(last_key=next_key)
    assert page_items[0]["id"] == 5


def test_keyset_last():
    items = [{"id": i} for i in range(5)]
    p = KeysetPaginator(items, per_page=10, key_field="id")
    page_items, next_key, has_next = p.get_page()
    assert has_next is False
    assert next_key is None


def test_infinite_scroll():
    items = list(range(25))
    scroll = InfiniteScroll(items, page_size=10)
    batch1, has_more = scroll.load_more()
    assert len(batch1) == 10
    assert has_more is True
    batch2, has_more = scroll.load_more()
    assert len(batch2) == 10
    batch3, has_more = scroll.load_more()
    assert len(batch3) == 5
    assert has_more is False


def test_infinite_scroll_reset():
    items = list(range(20))
    scroll = InfiniteScroll(items, page_size=5)
    scroll.load_more()
    scroll.load_more()
    assert scroll.loaded_count == 10
    scroll.reset()
    assert scroll.loaded_count == 0


def test_paginate_response():
    page = Page(items=[1, 2, 3], page=1, per_page=3, total=10, total_pages=4,
                has_next=True, has_prev=False, next_cursor="abc")
    resp = paginate_response(page, base_url="/api/items")
    assert "data" in resp
    assert resp["pagination"]["page"] == 1
    assert resp["pagination"]["next_cursor"] == "abc"
    assert "next_url" in resp["pagination"]


def test_all_pages():
    items = list(range(25))
    p = OffsetPaginator(items, per_page=10)
    pages = p.get_all_pages()
    assert len(pages) == 3
    assert len(pages[0].items) == 10
    assert len(pages[2].items) == 5
