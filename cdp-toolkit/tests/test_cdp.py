import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from cdp_client import CDPClient, CDPMouseEvents, CDPInput, CDPNavigation


def test_cdp_client_init():
    client = CDPClient("127.0.0.1", 9222)
    assert client.host == "127.0.0.1"
    assert client.port == 9222


def test_mouse_click_params():
    params = CDPMouseEvents.click_params(100, 200)
    assert params["x"] == 100
    assert params["y"] == 200
    assert params["type"] == "mousePressed"
    assert params["button"] == "left"


def test_mouse_release_params():
    params = CDPMouseEvents.release_params(100, 200)
    assert params["type"] == "mouseReleased"


def test_mouse_move_params():
    params = CDPMouseEvents.move_params(50, 75)
    assert params["x"] == 50
    assert params["type"] == "mouseMoved"


def test_insert_text():
    params = CDPInput.insert_text_params("hello world")
    assert params["text"] == "hello world"


def test_key_event():
    params = CDPInput.key_event_params("Enter", "keyDown")
    assert params["key"] == "Enter"
    assert params["type"] == "keyDown"


def test_native_setter_js():
    js = CDPInput.native_setter_js("#email", "test@test.com")
    assert "HTMLInputElement" in js
    assert "test@test.com" in js
    assert "nativeInputValueSetter" in js


def test_navigate_params():
    params = CDPNavigation.navigate_params("https://example.com")
    assert params["url"] == "https://example.com"


def test_evaluate_params():
    params = CDPNavigation.evaluate_params("document.title")
    assert params["expression"] == "document.title"
    assert params["returnByValue"] is True


def test_screenshot_params():
    params = CDPNavigation.screenshot_params("jpeg", 70)
    assert params["format"] == "jpeg"
    assert params["quality"] == 70
