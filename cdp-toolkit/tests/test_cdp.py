"""Tests for the CDP Toolkit helpers.

Network access is never required: :class:`CDPClient` HTTP calls are exercised
by monkeypatching ``urllib.request.urlopen`` with a small fake response.
"""
import io
import json
import os
import sys
import urllib.error

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from cdp_client import (  # noqa: E402
    CDPClient,
    CDPError,
    CDPInput,
    CDPMouseEvents,
    CDPNavigation,
)


class _FakeResponse(io.BytesIO):
    """Minimal context-manager stand-in for an ``http.client`` response."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


@pytest.fixture
def fake_urlopen(monkeypatch):
    """Patch ``urllib.request.urlopen`` to return a queued payload.

    Returns a setter callable; pass it the object to encode as the JSON body
    (or raw ``bytes``). The most recent request is recorded on ``.last_request``.
    """
    state: dict = {"payload": b"", "last_request": None}

    def _fake(req, timeout=None):
        state["last_request"] = req
        return _FakeResponse(state["payload"])

    def _set(payload):
        if isinstance(payload, (bytes, bytearray)):
            state["payload"] = bytes(payload)
        else:
            state["payload"] = json.dumps(payload).encode()

    monkeypatch.setattr("urllib.request.urlopen", _fake)
    _set.state = state  # type: ignore[attr-defined]
    return _set


# --------------------------------------------------------------------------- #
# CDPClient construction / validation
# --------------------------------------------------------------------------- #
def test_cdp_client_init():
    client = CDPClient("127.0.0.1", 9222)
    assert client.host == "127.0.0.1"
    assert client.port == 9222
    assert client.timeout == 5.0
    assert client.base_url == "http://127.0.0.1:9222"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"host": ""},
        {"port": 0},
        {"port": 70000},
        {"timeout": 0},
        {"timeout": -1},
    ],
)
def test_cdp_client_init_invalid(kwargs):
    with pytest.raises(ValueError):
        CDPClient(**kwargs)


def test_next_id_monotonic():
    client = CDPClient()
    assert client._next_id() == 1
    assert client._next_id() == 2
    assert client.msg_id == 2


# --------------------------------------------------------------------------- #
# CDPClient HTTP methods (mocked)
# --------------------------------------------------------------------------- #
def test_list_targets(fake_urlopen):
    fake_urlopen([{"type": "page", "id": "A"}])
    client = CDPClient()
    targets = client.list_targets()
    assert targets == [{"type": "page", "id": "A"}]
    assert fake_urlopen.state["last_request"].full_url == "http://127.0.0.1:9222/json"


def test_list_targets_wrong_type(fake_urlopen):
    fake_urlopen({"not": "a list"})
    with pytest.raises(CDPError):
        CDPClient().list_targets()


def test_get_ws_url(fake_urlopen):
    fake_urlopen(
        [
            {"type": "background_page"},
            {"type": "page", "webSocketDebuggerUrl": "ws://x/devtools/1"},
        ]
    )
    assert CDPClient().get_ws_url() == "ws://x/devtools/1"


def test_get_ws_url_missing(fake_urlopen):
    fake_urlopen([{"type": "background_page"}])
    with pytest.raises(CDPError):
        CDPClient().get_ws_url()


def test_create_target(fake_urlopen):
    fake_urlopen({"id": "new-tab", "type": "page"})
    client = CDPClient()
    result = client.create_target("https://example.com")
    assert result["id"] == "new-tab"
    req = fake_urlopen.state["last_request"]
    assert req.method == "PUT"
    assert "https%3A%2F%2Fexample.com" in req.full_url


def test_create_target_empty_url():
    with pytest.raises(ValueError):
        CDPClient().create_target("")


def test_close_target(fake_urlopen):
    fake_urlopen({"result": True})
    assert CDPClient().close_target("abc") is True
    assert "/json/close/abc" in fake_urlopen.state["last_request"].full_url


def test_close_target_empty():
    with pytest.raises(ValueError):
        CDPClient().close_target("")


def test_activate_target(fake_urlopen):
    fake_urlopen(b"")
    assert CDPClient().activate_target("abc") is True
    assert "/json/activate/abc" in fake_urlopen.state["last_request"].full_url


def test_activate_target_empty():
    with pytest.raises(ValueError):
        CDPClient().activate_target("")


def test_get_version(fake_urlopen):
    fake_urlopen({"Browser": "Chrome/120"})
    assert CDPClient().get_version()["Browser"] == "Chrome/120"


def test_request_network_error(monkeypatch):
    def _boom(req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _boom)
    with pytest.raises(CDPError):
        CDPClient().list_targets()


def test_request_invalid_json(fake_urlopen):
    fake_urlopen(b"<html>not json</html>")
    with pytest.raises(CDPError):
        CDPClient().get_version()


# --------------------------------------------------------------------------- #
# CDPMouseEvents
# --------------------------------------------------------------------------- #
def test_mouse_click_params():
    params = CDPMouseEvents.click_params(100, 200)
    assert params["x"] == 100
    assert params["y"] == 200
    assert params["type"] == "mousePressed"
    assert params["button"] == "left"
    assert params["clickCount"] == 1


def test_mouse_click_params_double():
    params = CDPMouseEvents.click_params(1, 2, button="right", click_count=2)
    assert params["button"] == "right"
    assert params["clickCount"] == 2


def test_mouse_release_params():
    params = CDPMouseEvents.release_params(100, 200)
    assert params["type"] == "mouseReleased"
    assert params["clickCount"] == 1


def test_mouse_move_params():
    params = CDPMouseEvents.move_params(50, 75)
    assert params["x"] == 50
    assert params["y"] == 75
    assert params["type"] == "mouseMoved"


# --------------------------------------------------------------------------- #
# CDPInput
# --------------------------------------------------------------------------- #
def test_insert_text():
    params = CDPInput.insert_text_params("hello world")
    assert params["text"] == "hello world"


def test_key_event():
    params = CDPInput.key_event_params("Enter", "keyDown")
    assert params["key"] == "Enter"
    assert params["type"] == "keyDown"


def test_key_event_default_type():
    assert CDPInput.key_event_params("a")["type"] == "keyDown"


def test_native_setter_js():
    js = CDPInput.native_setter_js("#email", "test@test.com")
    assert "HTMLInputElement" in js
    assert "test@test.com" in js
    assert "nativeInputValueSetter" in js


def test_native_setter_js_escapes_quotes():
    # A value containing a single quote must not break out of the JS literal.
    js = CDPInput.native_setter_js("#name", "O'Brien")
    assert "O'Brien" in js
    # Selector and value are JSON-encoded, so they appear double-quoted.
    assert '"#name"' in js


# --------------------------------------------------------------------------- #
# CDPNavigation
# --------------------------------------------------------------------------- #
def test_navigate_params():
    params = CDPNavigation.navigate_params("https://example.com")
    assert params["url"] == "https://example.com"


def test_navigate_params_empty():
    with pytest.raises(ValueError):
        CDPNavigation.navigate_params("")


def test_evaluate_params():
    params = CDPNavigation.evaluate_params("document.title")
    assert params["expression"] == "document.title"
    assert params["returnByValue"] is True


def test_screenshot_params():
    params = CDPNavigation.screenshot_params("jpeg", 70)
    assert params["format"] == "jpeg"
    assert params["quality"] == 70


def test_screenshot_params_defaults():
    params = CDPNavigation.screenshot_params()
    assert params["format"] == "png"
    assert params["quality"] == 80


@pytest.mark.parametrize("quality", [-1, 101])
def test_screenshot_params_invalid_quality(quality):
    with pytest.raises(ValueError):
        CDPNavigation.screenshot_params(quality=quality)


# --------------------------------------------------------------------------- #
# Error handling: timeouts and connection refused
# --------------------------------------------------------------------------- #

def test_request_connection_refused_error(monkeypatch):
    """A connection refused error from the OS must be wrapped in CDPError."""

    def _raise_refused(_req, timeout=None):
        raise ConnectionRefusedError(111, "Connection refused")

    monkeypatch.setattr("urllib.request.urlopen", _raise_refused)
    with pytest.raises(CDPError, match="Connection refused"):
        CDPClient().list_targets()


def test_request_timeout_error(monkeypatch):
    """A TimeoutError raised by urlopen must be wrapped in CDPError."""

    def _raise_timeout(_req, timeout=None):
        raise TimeoutError("timed out")

    monkeypatch.setattr("urllib.request.urlopen", _raise_timeout)
    with pytest.raises(CDPError, match="timed out"):
        CDPClient().list_targets()


def test_request_url_error_timeout(monkeypatch):
    """A URLError wrapping a timeout exception must be wrapped in CDPError."""

    def _raise_url_error(_req, timeout=None):
        raise urllib.error.URLError(TimeoutError("timed out"))

    monkeypatch.setattr("urllib.request.urlopen", _raise_url_error)
    with pytest.raises(CDPError, match="timed out"):
        CDPClient().list_targets()


def test_cdp_toolkit_package_re_exports():
    """The package must be importable as documented: ``from cdp_toolkit import ...``."""
    import cdp_toolkit

    assert callable(cdp_toolkit.CDPClient)
    assert callable(cdp_toolkit.CDPInput.insert_text_params)
    assert callable(cdp_toolkit.CDPMouseEvents.click_params)
    assert callable(cdp_toolkit.CDPNavigation.navigate_params)
    assert issubclass(cdp_toolkit.CDPError, Exception)


def test_cdp_toolkit_client_same_as_cdp_client():
    """The package public API must expose the same classes as ``cdp_client``."""
    import cdp_toolkit
    from cdp_client import CDPClient

    assert cdp_toolkit.CDPClient is CDPClient
