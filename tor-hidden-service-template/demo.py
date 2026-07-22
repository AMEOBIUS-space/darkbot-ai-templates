#!/usr/bin/env python3
"""Offline demo for Tor Hidden Service Setup — no network, no host changes."""
from __future__ import annotations

import base64
import hashlib

from setup import TorHiddenService


def demo() -> None:
    print("=" * 50)
    print("Tor Hidden Service Template — offline demo")
    print("=" * 50)
    print()

    print("Generating mock v3 .onion address (ed25519 shape)...")
    mock_pubkey = b"\x00" * 32
    checksum_data = b".onion checksum" + mock_pubkey + b"\x03"
    checksum = hashlib.sha3_256(checksum_data).digest()[:2]
    address_bytes = mock_pubkey + checksum + b"\x03"
    address = base64.b32encode(address_bytes).decode().lower().rstrip("=")
    print(f"  -> Address: {address}.onion")
    print(f"  -> Version: 3 (ed25519)")
    print()

    svc = TorHiddenService(service_name="demo", port=8080)
    print("torrc snippet:")
    for line in svc.generate_torrc_config().strip().splitlines():
        print(f"  {line}")
    print()

    print("nginx hardened flags:")
    nginx = svc.generate_nginx_config()
    for needle in ("access_log off", "server_tokens off", "X-Frame-Options DENY"):
        assert needle in nginx
        print(f"  ok: {needle}")
    print()

    print("docker-compose services:")
    compose = svc.generate_docker_compose()
    assert "tor:" in compose and "web:" in compose
    print("  ok: tor + web")
    print()

    print("hardening script length:", len(svc.generate_hardening_script()), "chars")
    print()
    print("v3 onion, nginx, hardening, Docker, PHP support")
    print("=" * 50)


if __name__ == "__main__":
    demo()
