#!/usr/bin/env python3
"""Tor Hidden Service Setup Template — deploy .onion site with nginx + Tor + security hardening."""
import os, subprocess, hashlib, base64, logging

logging.basicConfig(level=logging.INFO)

class TorHiddenService:
    """Deploy and manage Tor hidden services (.onion sites)."""
    
    def __init__(self, service_name: str = "darkbot", port: int = 80, tor_port: int = 80):
        self.service_name = service_name
        self.port = port
        self.tor_port = tor_port
        self.torrc_path = "/etc/tor/torrc"
        self.service_dir = f"/var/lib/tor/{service_name}"
    
    def generate_v3_onion_address(self) -> dict:
        """Generate v3 .onion address (56 chars) using ed25519 keys."""
        try:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            from cryptography.hazmat.primitives import serialization
            import base64 as b64
            
            # Generate ed25519 keypair
            private_key = Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Serialize
            priv_bytes = private_key.private_bytes(
                serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw,
                serialization.NoEncryption()
            )
            pub_bytes = public_key.public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw
            )
            
            # v3 onion address = base32(public_key) + checksum + version
            # Checksum = sha3_256(".onion checksum" + pubkey + version)[:2]
            import hashlib
            checksum_data = b".onion checksum" + pub_bytes + b"\x03"
            checksum = hashlib.sha3_256(checksum_data).digest()[:2]
            
            # Address = base32(pubkey + checksum + version_byte)
            address_bytes = pub_bytes + checksum + b"\x03"
            import base64 as b64mod
            # base32 encode (no padding)
            address = b64mod.b32encode(address_bytes).decode().lower().rstrip("=")
            
            return {
                "address": f"{address}.onion",
                "public_key": pub_bytes.hex(),
                "private_key": priv_bytes.hex(),
            }
        except ImportError:
            return {"error": "Install cryptography: pip install cryptography"}
    
    def generate_torrc_config(self) -> str:
        """Generate torrc configuration for hidden service."""
        return f"""# Hidden Service: {self.service_name}
HiddenServiceDir {self.service_dir}
HiddenServicePort {self.tor_port} 127.0.0.1:{self.port}
# v3 onion (default in Tor 0.3.5+)
HiddenServiceVersion 3
# Client authorization (optional)
# HiddenServiceAuthorizeClient basic {self.service_name}_clients
"""
    
    def generate_nginx_config(self, web_root: str = "/var/www/darkbot") -> str:
        """Generate nginx config for .onion site."""
        return f"""server {{
    listen 127.0.0.1:{self.port};
    server_name {self.service_name}.onion;
    
    root {web_root};
    index index.html index.php;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # Disable logging (privacy)
    access_log off;
    error_log off;
    
    # No server tokens
    server_tokens off;
    
    location / {{
        try_files $uri $uri/ =404;
    }}
    
    # PHP support (if needed)
    location ~ \.php$ {{
        fastcgi_pass unix:/run/php/php-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }}
}}
"""
    
    def generate_hardening_script(self) -> str:
        """Generate server hardening shell script."""
        return f"""#!/bin/bash
# Tor Hidden Service Hardening Script
set -e

# 1. Install Tor + nginx
apt-get update && apt-get install -y tor nginx

# 2. Create service directory
mkdir -p {self.service_dir}
chown debian-tor:debian-tor {self.service_dir}
chmod 700 {self.service_dir}

# 3. Create web root
mkdir -p /var/www/{self.service_name}
echo '<html><body><h1>{self.service_name} .onion</h1><p>DarkBot AI</p></body></html>' > /var/www/{self.service_name}/index.html

# 4. Configure Tor
cat >> {self.torrc_path} << 'TORRC'
{self.generate_torrc_config()}
TORRC

# 5. Configure nginx
cat > /etc/nginx/sites-available/{self.service_name} << 'NGINX'
{self.generate_nginx_config()}
NGINX
ln -sf /etc/nginx/sites-available/{self.service_name} /etc/nginx/sites-enabled/

# 6. Disable nginx default site
rm -f /etc/nginx/sites-enabled/default

# 7. Restart services
systemctl restart tor
systemctl restart nginx

# 8. Wait for .onion address
sleep 5
echo "=== .onion address ==="
cat {self.service_dir}/hostname

# 9. Firewall (allow only localhost)
ufw default deny incoming
ufw allow 22/tcp  # SSH
ufw enable

echo "=== Hardening complete ==="
echo "Onion address: $(cat {self.service_dir}/hostname)"
"""
    
    def generate_docker_compose(self) -> str:
        """Generate docker-compose.yml for isolated deployment."""
        return f"""version: '3.8'
services:
  tor:
    image: osminog/tor
    container_name: {self.service_name}-tor
    restart: always
    volumes:
      - tor-data:/var/lib/tor
      - ./torrc:/etc/tor/torrc:ro
    depends_on:
      - web
  
  web:
    image: nginx:alpine
    container_name: {self.service_name}-web
    restart: always
    volumes:
      - ./web:/usr/share/nginx/html:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    expose:
      - "{self.port}"

volumes:
  tor-data:
"""

def main():
    service = TorHiddenService(service_name="darkbot", port=8080)
    
    print("=== V3 Onion Address ===")
    addr = service.generate_v3_onion_address()
    print(f"Address: {addr.get('address', 'N/A')}")
    
    print("\n=== torrc config ===")
    print(service.generate_torrc_config())
    
    print("=== nginx config ===")
    print(service.generate_nginx_config()[:200] + "...")
    
    print("=== Docker Compose ===")
    print(service.generate_docker_compose()[:200] + "...")
    
    print("\n=== Hardening script available via generate_hardening_script() ===")

if __name__ == "__main__":
    main()
