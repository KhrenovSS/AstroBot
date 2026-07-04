import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.exceptions import EncryptionError

NONCE_LENGTH = 12
AES_KEY_LENGTH = 32


class AESCipher:
    """AES-256-GCM шифрование для PII-данных (AES-256-GCM encryption for PII data)."""

    def __init__(self, key_hex: str):
        if len(key_hex) != 64:
            raise EncryptionError(
                f"AES key must be 64 hex chars (32 bytes), got {len(key_hex)}"
            )
        key = bytes.fromhex(key_hex)
        self._aesgcm = AESGCM(key)

    @classmethod
    def generate_key(cls) -> str:
        """Сгенерировать новый 256-битный ключ в hex (Generate a new 256-bit key as hex string)."""
        return AESGCM.generate_key(bit_length=256).hex()

    def encrypt(self, plaintext: str) -> str:
        """Зашифровать строку. Возвращает nonce+ciphertext hex (Encrypt string)."""
        nonce = os.urandom(NONCE_LENGTH)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        return (nonce + ciphertext).hex()

    def decrypt(self, encrypted_hex: str) -> str:
        """Расшифровать hex-строку (Decrypt hex string back to plaintext)."""
        try:
            data = bytes.fromhex(encrypted_hex)
            nonce = data[:NONCE_LENGTH]
            ciphertext = data[NONCE_LENGTH:]
            return self._aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}") from e
