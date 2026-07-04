import pytest

from app.exceptions import EncryptionError
from app.infra.crypto.aes_cipher import AESCipher


class TestAESCipher:
    """Тесты AES-256-GCM шифрования (AES-256-GCM encryption tests)."""

    def setup_method(self):
        self.key = AESCipher.generate_key()
        self.cipher = AESCipher(self.key)

    def test_generate_key_returns_64_hex_chars(self):
        key = AESCipher.generate_key()
        assert len(key) == 64
        assert isinstance(key, str)

    def test_encrypt_decrypt_roundtrip(self):
        plaintext = "Hello, AstroBot!"
        encrypted = self.cipher.encrypt(plaintext)
        assert encrypted != plaintext
        decrypted = self.cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_russian_text(self):
        plaintext = "Привет, Астробот! 123"
        encrypted = self.cipher.encrypt(plaintext)
        decrypted = self.cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_long_text(self):
        plaintext = "x" * 10000
        encrypted = self.cipher.encrypt(plaintext)
        decrypted = self.cipher.decrypt(encrypted)
        assert decrypted == plaintext

    def test_decrypt_wrong_key_raises_error(self):
        plaintext = "secret data"
        encrypted = self.cipher.encrypt(plaintext)
        wrong_cipher = AESCipher(AESCipher.generate_key())
        with pytest.raises(EncryptionError):
            wrong_cipher.decrypt(encrypted)

    def test_decrypt_invalid_hex_raises_error(self):
        with pytest.raises(EncryptionError):
            self.cipher.decrypt("not-hex-string")

    def test_decrypt_tampered_ciphertext_raises_error(self):
        encrypted = self.cipher.encrypt("important")
        tampered = encrypted[:-4] + "0000"
        with pytest.raises(EncryptionError):
            self.cipher.decrypt(tampered)

    def test_init_with_invalid_key_length_raises_error(self):
        with pytest.raises(EncryptionError):
            AESCipher("tooshort")

    def test_each_encryption_produces_different_output(self):
        plaintext = "same text"
        e1 = self.cipher.encrypt(plaintext)
        e2 = self.cipher.encrypt(plaintext)
        assert e1 != e2
