"""Tests for HealthChecker template."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from darkbot_templates.templates.health_checker import HealthChecker


class TestHealthChecker:
    def test_up_endpoint(self):
        hc = HealthChecker(timeout=1.0)
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            r = hc.check("http://example.com")
        assert r["status"] == "up"
        assert r["status_code"] == 200
        assert r["latency_ms"] >= 0

    def test_down_endpoint(self):
        hc = HealthChecker(timeout=1.0)
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("conn refused")):
            r = hc.check("http://down.example.com")
        assert r["status"] == "down"
        assert r["error"] is not None

    def test_degraded_500(self):
        hc = HealthChecker(timeout=1.0)
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("url", 500, "ERR", {}, None)):
            r = hc.check("http://err.example.com")
        assert r["status"] == "down"
        assert r["status_code"] == 500

    def test_degraded_404(self):
        hc = HealthChecker(timeout=1.0)
        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.HTTPError("url", 404, "NF", {}, None)):
            r = hc.check("http://nf.example.com")
        assert r["status"] == "degraded"
        assert r["status_code"] == 404

    def test_uptime_percentage(self):
        hc = HealthChecker(timeout=1.0)
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        import urllib.error
        with patch("urllib.request.urlopen", return_value=mock_resp):
            hc.check("http://a.com")
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("x")):
            hc.check("http://b.com")
        with patch("urllib.request.urlopen", return_value=mock_resp):
            hc.check("http://c.com")
        assert hc.uptime_percentage == 66.7

    def test_history_capped(self):
        hc = HealthChecker(timeout=1.0)
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            for i in range(105):
                hc.check(f"http://h{i}.com")
        assert len(hc.history) == 100

    def test_reset(self):
        hc = HealthChecker(timeout=1.0)
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = MagicMock(return_value=mock_resp)
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=mock_resp):
            hc.check("http://x.com")
        assert len(hc.history) == 1
        hc.reset()
        assert len(hc.history) == 0
