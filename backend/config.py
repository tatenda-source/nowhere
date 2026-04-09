import os
import secrets

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, model_validator


_INSECURE_DEFAULTS = {"devsecret", "changeme", "secret", ""}


class Settings(BaseSettings):
    APP_NAME: str = "nowhere-backend"
    DEBUG: bool = Field(default=False, validation_alias="DEBUG")
    REDIS_DSN: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_DSN")
    POSTGRES_DSN: str = Field(
        default="sqlite+aiosqlite:///./nowhere.db",
        validation_alias="POSTGRES_DSN",
    )
    POSTGRES_ENABLED: bool = Field(default=False, validation_alias="POSTGRES_ENABLED")
    DEVICE_TOKEN_SECRET: str = Field(default="devsecret", validation_alias="DEVICE_TOKEN_SECRET")
    REDIS_TTL_SECONDS: int = Field(default=60 * 60 * 6, validation_alias="REDIS_TTL_SECONDS")

    # Explicit JWT settings (lowercase to match usage in jwt.py)
    jwt_secret: str = Field(default="devsecret", validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")

    # CORS — comma-separated allowed origins (e.g. "https://nowhere.app,https://www.nowhere.app")
    ALLOWED_ORIGINS: str = Field(default="", validation_alias="ALLOWED_ORIGINS")

    # Ranking weights
    RANKING_W_DIST: float = Field(default=1.0, validation_alias="RANKING_W_DIST")
    RANKING_W_FRESH: float = Field(default=2.0, validation_alias="RANKING_W_FRESH")
    RANKING_W_POP: float = Field(default=0.5, validation_alias="RANKING_W_POP")
    RANKING_DECAY_SECONDS: int = Field(default=86400, validation_alias="RANKING_DECAY_SECONDS")

    model_config = ConfigDict(env_file=".env")

    @model_validator(mode="after")
    def _check_secrets(self) -> "Settings":
        """Refuse to start with insecure secrets outside DEBUG mode."""
        if not self.DEBUG:
            if self.jwt_secret in _INSECURE_DEFAULTS:
                raise ValueError(
                    "JWT_SECRET must be set to a strong, random value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
                )
            if self.DEVICE_TOKEN_SECRET in _INSECURE_DEFAULTS:
                raise ValueError(
                    "DEVICE_TOKEN_SECRET must be set to a strong, random value in production."
                )
        return self


_settings = Settings()


def get_settings() -> Settings:
    return _settings


settings = _settings
# Backwards-compatible aliases for older code expecting different names
def _ensure_compat_aliases(s: Settings):
    # provide camel/other-style aliases used across the codebase
    try:
        setattr(s, "postgres_url", getattr(s, "POSTGRES_DSN"))
    except Exception:
        pass
    try:
        setattr(s, "redis_url", getattr(s, "REDIS_DSN"))
    except Exception:
        pass
    try:
        # older code expects `app_name` lowercased
        setattr(s, "app_name", getattr(s, "APP_NAME"))
    except Exception:
        pass
    
    try:
        if not hasattr(s, "jwt_secret"):
            setattr(s, "jwt_secret", getattr(s, "JWT_SECRET"))
        if not hasattr(s, "jwt_algorithm"):
            setattr(s, "jwt_algorithm", getattr(s, "JWT_ALGORITHM"))
    except Exception:
        pass


_ensure_compat_aliases(settings)
