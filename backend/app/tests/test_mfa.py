from __future__ import annotations

import pytest


def _login(client, email: str, password: str) -> dict:
    res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()


def _get_token(client, email: str, password: str) -> str:
    from app.core.database import get_sessionmaker
    from app.core.security import create_access_token
    from app.models.user import User
    from sqlalchemy import select

    db = get_sessionmaker()()
    try:
        user = db.scalar(select(User).where(User.email == email))
        return create_access_token(
            subject=str(user.id),
            tenant_id=str(user.tenant_id) if user.tenant_id else None,
            role="cliente",
        )
    finally:
        db.close()


def test_login_without_mfa_returns_token_pair(client):
    """Normal login (no MFA) returns access_token and refresh_token."""
    data = _login(client, "cliente@teste.local", "senha12345")
    assert "access_token" in data
    assert "refresh_token" in data
    assert data.get("mfa_required") is None


def test_totp_enable_returns_qr_uri_and_secret(client):
    """POST /auth/totp/enable returns otpauth_uri and secret."""
    token = _get_token(client, "cliente@teste.local", "senha12345")
    res = client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "otpauth_uri" in data
    assert "secret" in data
    assert data["otpauth_uri"].startswith("otpauth://totp/")


def test_totp_verify_with_valid_code_enables_mfa(client):
    """POST /auth/totp/verify with valid code sets totp_enabled=True."""
    import pyotp

    token = _get_token(client, "cliente@teste.local", "senha12345")

    # Enable TOTP
    enable_res = client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    assert enable_res.status_code == 200
    secret = enable_res.json()["secret"]

    # Verify with valid code
    code = pyotp.TOTP(secret).now()
    verify_res = client.post(
        "/api/v1/auth/totp/verify",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["totp_enabled"] is True


def test_totp_verify_with_invalid_code_returns_401(client):
    """POST /auth/totp/verify with invalid code returns 401."""
    token = _get_token(client, "cliente@teste.local", "senha12345")

    client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})

    res = client.post(
        "/api/v1/auth/totp/verify",
        json={"code": "000000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401


def test_login_with_mfa_enabled_returns_mfa_required(client):
    """Login with MFA enabled returns mfa_required=True and mfa_token."""
    import pyotp

    token = _get_token(client, "cliente@teste.local", "senha12345")

    # Enable and verify TOTP
    enable_res = client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    secret = enable_res.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post(
        "/api/v1/auth/totp/verify",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Now login — should require MFA
    login_data = _login(client, "cliente@teste.local", "senha12345")
    assert login_data.get("mfa_required") is True
    assert "mfa_token" in login_data
    assert "access_token" not in login_data


def test_totp_login_with_valid_code_returns_token_pair(client):
    """POST /auth/totp/login with valid code returns access_token and refresh_token."""
    import pyotp

    token = _get_token(client, "cliente@teste.local", "senha12345")

    # Enable and verify TOTP
    enable_res = client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    secret = enable_res.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post(
        "/api/v1/auth/totp/verify",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Login to get mfa_token
    login_data = _login(client, "cliente@teste.local", "senha12345")
    mfa_token = login_data["mfa_token"]

    # Complete MFA login
    totp_code = pyotp.TOTP(secret).now()
    res = client.post(
        "/api/v1/auth/totp/login",
        json={"mfa_token": mfa_token, "code": totp_code},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_totp_login_with_invalid_code_returns_401(client):
    """POST /auth/totp/login with invalid code returns 401."""
    import pyotp

    token = _get_token(client, "cliente@teste.local", "senha12345")

    # Enable and verify TOTP
    enable_res = client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    secret = enable_res.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post(
        "/api/v1/auth/totp/verify",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Login to get mfa_token
    login_data = _login(client, "cliente@teste.local", "senha12345")
    mfa_token = login_data["mfa_token"]

    # Try with wrong code
    res = client.post(
        "/api/v1/auth/totp/login",
        json={"mfa_token": mfa_token, "code": "000000"},
    )
    assert res.status_code == 401


def test_totp_disable_with_valid_credentials(client):
    """POST /auth/totp/disable with valid password and code disables MFA."""
    import pyotp

    token = _get_token(client, "cliente@teste.local", "senha12345")

    # Enable and verify TOTP
    enable_res = client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    secret = enable_res.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post(
        "/api/v1/auth/totp/verify",
        json={"code": code},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Disable TOTP
    disable_code = pyotp.TOTP(secret).now()
    res = client.post(
        "/api/v1/auth/totp/disable",
        json={"password": "senha12345", "code": disable_code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["totp_enabled"] is False

    # Login should now return token pair directly (no MFA)
    login_data = _login(client, "cliente@teste.local", "senha12345")
    assert "access_token" in login_data
    assert login_data.get("mfa_required") is None


def test_totp_disable_with_wrong_password_returns_401(client):
    """POST /auth/totp/disable with wrong password returns 401."""
    import pyotp

    token = _get_token(client, "cliente@teste.local", "senha12345")

    enable_res = client.post("/api/v1/auth/totp/enable", headers={"Authorization": f"Bearer {token}"})
    secret = enable_res.json()["secret"]
    code = pyotp.TOTP(secret).now()
    client.post("/api/v1/auth/totp/verify", json={"code": code}, headers={"Authorization": f"Bearer {token}"})

    disable_code = pyotp.TOTP(secret).now()
    res = client.post(
        "/api/v1/auth/totp/disable",
        json={"password": "wrongpassword", "code": disable_code},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401
