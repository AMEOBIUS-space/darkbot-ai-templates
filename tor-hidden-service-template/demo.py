#!/usr/bin/env python3
"""Demo for Tor Hidden Service Setup — generates v3 onion address, configs."""
import hashlib, base64

def demo():
    print("=" * 50)
    print("🌐 DarkBot AI — Tor Hidden Service Demo")
    print("=" * 50)
    print()
    
    # Simulate v3 onion generation
    print("🔑 Generating v3 .onion address (ed25519)...")
    mock_pubkey = b'\x00' * 32  # Mock key
    checksum_data = b".onion checksum" + mock_pubkey + b"\x03"
    checksum = hashlib.sha3_256(checksum_data).digest()[:2]
    address_bytes = mock_pubkey + checksum + b"\x03"
    address = base64.b32encode(address_bytes).decode().lower().rstrip("=")
    print(f"  → Address: {address}.onion")
    print(f"  → Public key: {mock_pubkey.hex()[:32]}...")
    print(f"  → Version: 3 (ed25519)")
    print()
    
    # torrc
    print("📝 torrc config:")
    print("  HiddenServiceDir /var/lib/tor/darkbot")
    print("  HiddenServicePort 80 127.0.0.1:8080")
    print("  HiddenServiceVersion 3")
    print()
    
    # nginx
    print("🌐 nginx config (hardened):")
    print("  listen 127.0.0.1:8080")
    print("  access_log off")
    print("  server_tokens off")
    print("  X-Content-Type-Options: nosniff")
    print("  X-Frame-Options: DENY")
    print()
    
    # Docker
    print("🐳 Docker Compose:")
    print("  tor: osminog/tor (SOCKS5)")
    print("  web: nginx:alpine (static)")
    print()
    
    # Hardening
    print("🛡 Hardening:")
    print("  → UFW: deny all except SSH")
    print("  → No server tokens")
    print("  → No access logs")
    print("  → Client authorization (optional)")
    print()
    
    print("✅ v3 onion, nginx, hardening, Docker, PHP support")
    print("Buy template: @darkbot_ai_bot | $89 | BTC/USDT/ETH/XMR")
    print("=" * 50)

if __name__ == "__main__":
    demo()
