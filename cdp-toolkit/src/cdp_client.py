"""CDP Toolkit — Chrome DevTools Protocol automation without external deps."""
import json
import socket
import base64
import urllib.request
from typing import Any, Dict, Optional, List


class CDPClient:
    """Minimal CDP client using raw WebSocket protocol."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9222):
        self.host = host
        self.port = port
        self.msg_id = 0
        self.ws = None

    def _get_ws_url(self) -> str:
        """Get WebSocket debugger URL from CDP HTTP endpoint."""
        url = f"http://{self.host}:{self.port}/json"
        resp = urllib.request.urlopen(url, timeout=5)
        tabs = json.loads(resp.read())
        for tab in tabs:
            if tab.get("type") == "page":
                return tab["webSocketDebuggerUrl"]
        raise ConnectionError("No page tab found")

    def _next_id(self) -> int:
        self.msg_id += 1
        return self.msg_id

    def list_targets(self) -> List[Dict]:
        """List all browser targets via HTTP endpoint."""
        url = f"http://{self.host}:{self.port}/json"
        resp = urllib.request.urlopen(url, timeout=5)
        return json.loads(resp.read())

    def create_target(self, url: str) -> Dict:
        """Create a new browser tab."""
        encoded = urllib.parse.quote(url, safe="")
        req = urllib.request.Request(
            f"http://{self.host}:{self.port}/json/new?{encoded}",
            method="PUT"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read())

    def close_target(self, target_id: str) -> bool:
        """Close a browser tab by target ID."""
        req = urllib.request.Request(
            f"http://{self.host}:{self.port}/json/close/{target_id}",
            method="GET"
        )
        resp = urllib.request.urlopen(req, timeout=5)
        result = json.loads(resp.read())
        return result.get("result", False)

    def activate_target(self, target_id: str) -> bool:
        """Activate a browser tab."""
        req = urllib.request.Request(
            f"http://{self.host}:{self.port}/json/activate/{target_id}",
            method="GET"
        )
        resp = urllib.request.urlopen(req, timeout=5)
        return True

    def get_version(self) -> Dict:
        """Get browser version info."""
        url = f"http://{self.host}:{self.port}/json/version"
        resp = urllib.request.urlopen(url, timeout=5)
        return json.loads(resp.read())


class CDPMouseEvents:
    """CDP mouse event helpers — calculates coordinates for clicks."""

    @staticmethod
    def click_params(x: int, y: int, button: str = "left", click_count: int = 1) -> Dict:
        return {
            "type": "mousePressed",
            "x": x,
            "y": y,
            "button": button,
            "clickCount": click_count,
        }

    @staticmethod
    def release_params(x: int, y: int, button: str = "left") -> Dict:
        return {
            "type": "mouseReleased",
            "x": x,
            "y": y,
            "button": button,
            "clickCount": 1,
        }

    @staticmethod
    def move_params(x: int, y: int) -> Dict:
        return {"type": "mouseMoved", "x": x, "y": y}


class CDPInput:
    """CDP input helpers for text injection and key events."""

    @staticmethod
    def insert_text_params(text: str) -> Dict:
        return {"text": text}

    @staticmethod
    def key_event_params(key: str, type: str = "keyDown") -> Dict:
        return {"type": type, "key": key}

    @staticmethod
    def native_setter_js(selector: str, value: str) -> str:
        """JavaScript for React/Vue native value setter."""
        return f"""
        (function() {{
            var el = document.querySelector('{selector}');
            if (!el) return 'Element not found';
            var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(el, '{value}');
            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
            el.dispatchEvent(new Event('change', {{ bubbles: true }}));
            return 'OK';
        }})()
        """


class CDPNavigation:
    """CDP navigation helpers."""

    @staticmethod
    def navigate_params(url: str) -> Dict:
        return {"url": url}

    @staticmethod
    def evaluate_params(expression: str) -> Dict:
        return {"expression": expression, "returnByValue": True}

    @staticmethod
    def screenshot_params(format: str = "png", quality: int = 80) -> Dict:
        return {"format": format, "quality": quality}
