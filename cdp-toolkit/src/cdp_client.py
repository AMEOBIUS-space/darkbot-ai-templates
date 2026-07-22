"""CDP Toolkit — Chrome DevTools Protocol automation without external deps.

This module provides small, dependency-free helpers for driving a browser
through the Chrome DevTools Protocol (CDP):

- :class:`CDPClient` talks to the CDP HTTP endpoint to manage tabs (targets).
- :class:`CDPMouseEvents` builds ``Input.dispatchMouseEvent`` parameters.
- :class:`CDPInput` builds text/key input parameters and native-setter JS.
- :class:`CDPNavigation` builds ``Page``/``Runtime`` parameters.

Everything relies only on the Python standard library.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

__all__ = [
    "CDPError",
    "CDPClient",
    "CDPMouseEvents",
    "CDPInput",
    "CDPNavigation",
]

# Type alias for a decoded JSON object returned by the CDP HTTP endpoint.
JSONDict = dict[str, Any]


class CDPError(RuntimeError):
    """Raised when a CDP HTTP request fails or returns an unexpected result."""


class CDPClient:
    """Minimal CDP client that manages targets via the HTTP endpoint.

    Args:
        host: Host where the browser exposes its remote-debugging endpoint.
        port: Remote-debugging port (Chrome's default is ``9222``).
        timeout: Default timeout, in seconds, applied to HTTP requests.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9222,
        timeout: float = 5.0,
    ) -> None:
        if not host:
            raise ValueError("host must be a non-empty string")
        if not 0 < port < 65536:
            raise ValueError(f"port must be in range 1-65535, got {port}")
        if timeout <= 0:
            raise ValueError(f"timeout must be positive, got {timeout}")
        self.host = host
        self.port = port
        self.timeout = timeout
        self.msg_id = 0

    @property
    def base_url(self) -> str:
        """Base URL of the CDP HTTP endpoint (``http://host:port``)."""
        return f"http://{self.host}:{self.port}"

    def _request(self, path: str, method: str = "GET") -> Any:
        """Perform an HTTP request against the CDP endpoint and decode JSON.

        Args:
            path: Path (and query) appended to :attr:`base_url`.
            method: HTTP method to use.

        Returns:
            The decoded JSON payload.

        Raises:
            CDPError: If the request fails or the response is not valid JSON.
        """
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
        except urllib.error.URLError as exc:
            raise CDPError(f"CDP request to {url} failed: {exc}") from exc
        except OSError as exc:  # pragma: no cover - network edge cases
            raise CDPError(f"CDP request to {url} failed: {exc}") from exc

        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CDPError(f"Invalid JSON from {url}: {exc}") from exc

    def _next_id(self) -> int:
        """Return a monotonically increasing message id for CDP commands."""
        self.msg_id += 1
        return self.msg_id

    def get_ws_url(self) -> str:
        """Return the WebSocket debugger URL of the first page target.

        Returns:
            The ``webSocketDebuggerUrl`` of the first target of type ``page``.

        Raises:
            CDPError: If no page target is available.
        """
        for target in self.list_targets():
            if target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                return target["webSocketDebuggerUrl"]
        raise CDPError("No page target with a WebSocket debugger URL was found")

    def list_targets(self) -> list[JSONDict]:
        """List all browser targets exposed by the HTTP endpoint.

        Returns:
            A list of target descriptors.

        Raises:
            CDPError: If the endpoint is unreachable or returns unexpected data.
        """
        result = self._request("/json")
        if not isinstance(result, list):
            raise CDPError(f"Expected a list of targets, got {type(result).__name__}")
        return result

    def create_target(self, url: str) -> JSONDict:
        """Create (open) a new browser tab pointing at ``url``.

        Args:
            url: The URL to open in the new tab.

        Returns:
            The descriptor of the newly created target.

        Raises:
            ValueError: If ``url`` is empty.
            CDPError: If the request fails or returns unexpected data.
        """
        if not url:
            raise ValueError("url must be a non-empty string")
        encoded = urllib.parse.quote(url, safe="")
        result = self._request(f"/json/new?{encoded}", method="PUT")
        if not isinstance(result, dict):
            raise CDPError(f"Expected a target descriptor, got {type(result).__name__}")
        return result

    def close_target(self, target_id: str) -> bool:
        """Close a browser tab by its target id.

        Args:
            target_id: The id of the target to close.

        Returns:
            ``True`` if the endpoint acknowledged the close request.

        Raises:
            ValueError: If ``target_id`` is empty.
            CDPError: If the request fails.
        """
        if not target_id:
            raise ValueError("target_id must be a non-empty string")
        self._request(f"/json/close/{target_id}")
        return True

    def activate_target(self, target_id: str) -> bool:
        """Bring a browser tab to the foreground by its target id.

        Args:
            target_id: The id of the target to activate.

        Returns:
            ``True`` if the endpoint acknowledged the activate request.

        Raises:
            ValueError: If ``target_id`` is empty.
            CDPError: If the request fails.
        """
        if not target_id:
            raise ValueError("target_id must be a non-empty string")
        self._request(f"/json/activate/{target_id}")
        return True

    def get_version(self) -> JSONDict:
        """Return browser/protocol version information.

        Returns:
            A mapping describing the browser and protocol versions.

        Raises:
            CDPError: If the request fails or returns unexpected data.
        """
        result = self._request("/json/version")
        if not isinstance(result, dict):
            raise CDPError(f"Expected version info, got {type(result).__name__}")
        return result


class CDPMouseEvents:
    """Builders for ``Input.dispatchMouseEvent`` parameter dictionaries."""

    @staticmethod
    def click_params(
        x: int,
        y: int,
        button: str = "left",
        click_count: int = 1,
    ) -> JSONDict:
        """Build parameters for a ``mousePressed`` event.

        Args:
            x: X coordinate, in CSS pixels.
            y: Y coordinate, in CSS pixels.
            button: Mouse button (``left``, ``middle``, ``right``, ``none``).
            click_count: Number of consecutive clicks (2 for a double-click).

        Returns:
            The event parameter dictionary.
        """
        return {
            "type": "mousePressed",
            "x": x,
            "y": y,
            "button": button,
            "clickCount": click_count,
        }

    @staticmethod
    def release_params(x: int, y: int, button: str = "left") -> JSONDict:
        """Build parameters for a ``mouseReleased`` event.

        Args:
            x: X coordinate, in CSS pixels.
            y: Y coordinate, in CSS pixels.
            button: Mouse button that was released.

        Returns:
            The event parameter dictionary.
        """
        return {
            "type": "mouseReleased",
            "x": x,
            "y": y,
            "button": button,
            "clickCount": 1,
        }

    @staticmethod
    def move_params(x: int, y: int) -> JSONDict:
        """Build parameters for a ``mouseMoved`` event.

        Args:
            x: X coordinate, in CSS pixels.
            y: Y coordinate, in CSS pixels.

        Returns:
            The event parameter dictionary.
        """
        return {"type": "mouseMoved", "x": x, "y": y}


class CDPInput:
    """Builders for text/key input parameters and native-setter JavaScript."""

    @staticmethod
    def insert_text_params(text: str) -> JSONDict:
        """Build parameters for ``Input.insertText``.

        Args:
            text: The text to insert at the current focus.

        Returns:
            The parameter dictionary.
        """
        return {"text": text}

    @staticmethod
    def key_event_params(key: str, type: str = "keyDown") -> JSONDict:
        """Build parameters for ``Input.dispatchKeyEvent``.

        Args:
            key: The key value (e.g. ``"Enter"``, ``"a"``).
            type: The event type (``keyDown``, ``keyUp``, ``rawKeyDown``).

        Returns:
            The parameter dictionary.
        """
        return {"type": type, "key": key}

    @staticmethod
    def native_setter_js(selector: str, value: str) -> str:
        """Return JS that sets an input's value via React/Vue's native setter.

        Frameworks such as React track input values internally, so assigning
        ``el.value`` directly is ignored. This uses the native ``value`` setter
        and dispatches ``input``/``change`` events so the framework updates.

        Args:
            selector: A CSS selector matching the target ``<input>`` element.
            value: The value to assign to the element.

        Returns:
            A self-invoking JavaScript expression suitable for
            ``Runtime.evaluate``. Both ``selector`` and ``value`` are
            JSON-encoded to guard against quote/escape injection.
        """
        selector_literal = json.dumps(selector)
        value_literal = json.dumps(value)
        return f"""
        (function() {{
            var el = document.querySelector({selector_literal});
            if (!el) return 'Element not found';
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(el, {value_literal});
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return 'OK';
        }})()
        """


class CDPNavigation:
    """Builders for navigation, evaluation, and screenshot parameters."""

    @staticmethod
    def navigate_params(url: str) -> JSONDict:
        """Build parameters for ``Page.navigate``.

        Args:
            url: The URL to navigate the page to.

        Returns:
            The parameter dictionary.

        Raises:
            ValueError: If ``url`` is empty.
        """
        if not url:
            raise ValueError("url must be a non-empty string")
        return {"url": url}

    @staticmethod
    def evaluate_params(expression: str) -> JSONDict:
        """Build parameters for ``Runtime.evaluate``.

        Args:
            expression: The JavaScript expression to evaluate.

        Returns:
            The parameter dictionary, requesting the result by value.
        """
        return {"expression": expression, "returnByValue": True}

    @staticmethod
    def screenshot_params(format: str = "png", quality: int = 80) -> JSONDict:
        """Build parameters for ``Page.captureScreenshot``.

        Args:
            format: Image format (``png`` or ``jpeg``).
            quality: Compression quality (0-100), only used for ``jpeg``.

        Returns:
            The parameter dictionary.

        Raises:
            ValueError: If ``quality`` is outside the 0-100 range.
        """
        if not 0 <= quality <= 100:
            raise ValueError(f"quality must be in range 0-100, got {quality}")
        return {"format": format, "quality": quality}
