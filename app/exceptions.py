class AstroBotError(Exception):
    """Base exception for all AstroBot errors."""


class ConfigurationError(AstroBotError):
    """Raised when required configuration is missing or invalid."""


class NotFoundError(AstroBotError):
    """Raised when an entity is not found."""


class ValidationError(AstroBotError):
    """Raised when input validation fails."""


class PaymentError(AstroBotError):
    """Raised on payment processing failures."""


class RateLimitExceeded(AstroBotError):
    """Raised when a user exceeds rate limits."""


class EncryptionError(AstroBotError):
    """Raised on encryption/decryption failures."""


class LLMProviderError(AstroBotError):
    """Raised when an LLM API call fails."""


class GeocodingError(AstroBotError):
    """Raised when geocoding fails."""


class AuthenticationError(AstroBotError):
    """Raised when API key or token is invalid."""


class SessionEndError(AstroBotError):
    """Raised when session termination fails."""


class MemoryConflictError(AstroBotError):
    """Raised when memory summary version conflict occurs."""
