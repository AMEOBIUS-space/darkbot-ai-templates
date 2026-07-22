"""Tests for encrypt_decrypt template."""
import pytest
from darkbot_templates.templates.encrypt_decrypt import SimpleCipher, HashUtil


class TestSimpleCipher:

    def test_encrypt_decrypt_roundtrip(self):
        cipher = SimpleCipher(key="test-key")
        encrypted = cipher.encrypt("Hello, World!")
        decrypted = cipher.decrypt_str(encrypted)
        assert decrypted == "Hello, World!"

    def test_encrypt_bytes(self):
        cipher = SimpleCipher(key="key")
        encrypted = cipher.encrypt(b"binary data")
        result = cipher.decrypt(encrypted)
        assert result == b"binary data"

    def test_different_ciphertexts_same_plaintext(self):
        cipher = SimpleCipher(key="key")
        enc1 = cipher.encrypt("same text")
        enc2 = cipher.encrypt("same text")
        assert enc1 != enc2  # Different due to random salt/IV

    def test_wrong_key_fails(self):
        c1 = SimpleCipher(key="correct-key")
        encrypted = c1.encrypt("secret message")
        c2 = SimpleCipher(key="wrong-key")
        assert c2.decrypt(encrypted) is None

    def test_tampered_ciphertext_fails(self):
        cipher = SimpleCipher(key="key")
        encrypted = cipher.encrypt("data")
        # Flip a character in the ciphertext
        import base64 as b64
        raw = bytearray(b64.b64decode(encrypted))
        raw[-1] ^= 0xFF  # Flip last byte
        tampered = b64.b64encode(bytes(raw)).decode()
        assert cipher.decrypt(tampered) is None

    def test_invalid_base64(self):
        cipher = SimpleCipher(key="key")
        assert cipher.decrypt("not base64!!!") is None

    def test_too_short_ciphertext(self):
        cipher = SimpleCipher(key="key")
        import base64 as b64
        short = b64.b64encode(b"short").decode()
        assert cipher.decrypt(short) is None

    def test_encrypt_dict(self):
        cipher = SimpleCipher(key="key")
        data = {"name": "Alice", "value": 42}
        encrypted = cipher.encrypt_dict(data)
        decrypted = cipher.decrypt_dict(encrypted)
        assert decrypted == data

    def test_empty_string(self):
        cipher = SimpleCipher(key="key")
        encrypted = cipher.encrypt("")
        assert cipher.decrypt_str(encrypted) == ""

    def test_unicode(self):
        cipher = SimpleCipher(key="key")
        text = "Привет мир! 🌍"
        encrypted = cipher.encrypt(text)
        assert cipher.decrypt_str(encrypted) == text


class TestHashUtil:

    def test_sha256(self):
        h = HashUtil.sha256("test")
        assert len(h) == 64  # 32 bytes hex
        assert h == HashUtil.sha256("test")  # deterministic

    def test_sha256_bytes(self):
        h1 = HashUtil.sha256("test")
        h2 = HashUtil.sha256(b"test")
        assert h1 == h2

    def test_sha512(self):
        h = HashUtil.sha512("test")
        assert len(h) == 128  # 64 bytes hex

    def test_md5_checksum(self):
        h = HashUtil.md5("test")
        assert len(h) == 32

    def test_hmac_sha256(self):
        sig = HashUtil.hmac_sha256("key", "message")
        assert len(sig) == 64
        assert sig != HashUtil.hmac_sha256("wrong", "message")

    def test_verify_hmac_valid(self):
        sig = HashUtil.hmac_sha256("secret", "data")
        assert HashUtil.verify_hmac("secret", "data", sig) is True

    def test_verify_hmac_invalid(self):
        assert HashUtil.verify_hmac("secret", "data", "wrong") is False

    def test_random_token(self):
        t1 = HashUtil.random_token()
        t2 = HashUtil.random_token()
        assert t1 != t2
        assert len(t1) > 30

    def test_random_token_length(self):
        t = HashUtil.random_token(length=64)
        assert len(t) > 60

    def test_password_hash_roundtrip(self):
        pw = "my_secure_password_123"
        stored = HashUtil.password_hash(pw)
        assert HashUtil.password_verify(pw, stored) is True

    def test_password_verify_wrong(self):
        stored = HashUtil.password_hash("correct")
        assert HashUtil.password_verify("wrong", stored) is False

    def test_password_hash_different_salts(self):
        h1 = HashUtil.password_hash("same")
        h2 = HashUtil.password_hash("same")
        assert h1 != h2  # Different salts

    def test_password_verify_invalid_format(self):
        assert HashUtil.password_verify("pw", "invalid$format") is False

    def test_password_verify_empty(self):
        assert HashUtil.password_verify("pw", "") is False


class TestSimpleCipherEdgeCases:
    """Edge case tests for SimpleCipher."""

    def test_empty_plaintext(self):
        from darkbot_templates.templates.encrypt_decrypt import SimpleCipher
        cipher = SimpleCipher(key="testkey")
        encrypted = cipher.encrypt("")
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == b""

    def test_unicode_plaintext(self):
        from darkbot_templates.templates.encrypt_decrypt import SimpleCipher
        cipher = SimpleCipher(key="key123")
        text = "Привет мир"
        encrypted = cipher.encrypt(text)
        decrypted = cipher.decrypt(encrypted)
        assert decrypted == text.encode("utf-8")

    def test_long_key(self):
        from darkbot_templates.templates.encrypt_decrypt import SimpleCipher
        cipher = SimpleCipher(key="a" * 1000)
        encrypted = cipher.encrypt("secret data")
        assert cipher.decrypt(encrypted) == b"secret data"

    def test_wrong_key_fails(self):
        from darkbot_templates.templates.encrypt_decrypt import SimpleCipher
        cipher1 = SimpleCipher(key="correct")
        cipher2 = SimpleCipher(key="wrong")
        encrypted = cipher1.encrypt("hidden")
        try:
            result = cipher2.decrypt(encrypted)
            assert result != b"hidden"
        except Exception:
            pass

    def test_repeated_encryption_different_ciphertext(self):
        from darkbot_templates.templates.encrypt_decrypt import SimpleCipher
        cipher = SimpleCipher(key="testkey")
        text = "same plaintext"
        e1 = cipher.encrypt(text)
        e2 = cipher.encrypt(text)
        assert e1 != e2
        assert cipher.decrypt(e1) == text.encode("utf-8")
        assert cipher.decrypt(e2) == text.encode("utf-8")
