from __future__ import annotations

import pytest
from app.core.config import Settings


def test_validate_production_rejects_default_jwt_secret():
    """Application must not start in production with the default JWT secret."""
    s = Settings(jwt_secret="change-me", app_env="production", seed_on_startup=False)
    with pytest.raises(RuntimeError, match="JWT_SECRET must be changed"):
        s.validate_for_production()


def test_validate_production_rejects_seed_on_startup():
    """SEED_ON_STARTUP=true must be blocked outside local environment."""
    s = Settings(jwt_secret="a-real-secret-value", app_env="production", seed_on_startup=True)
    with pytest.raises(RuntimeError, match="SEED_ON_STARTUP=true is not allowed"):
        s.validate_for_production()


def test_validate_local_allows_default_jwt_secret():
    """Local environment should allow the default JWT secret for development convenience."""
    s = Settings(jwt_secret="change-me", app_env="local", seed_on_startup=True)
    # Should not raise
    s.validate_for_production()


def test_validate_test_env_allows_default_jwt_secret():
    """Test environment should allow the default JWT secret."""
    s = Settings(jwt_secret="change-me", app_env="test", seed_on_startup=False)
    # Should not raise
    s.validate_for_production()


def test_validate_production_with_valid_config():
    """Production with proper config should pass validation."""
    s = Settings(jwt_secret="a-strong-random-secret-value-here", app_env="production", seed_on_startup=False)
    # Should not raise
    s.validate_for_production()
