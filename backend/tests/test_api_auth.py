import pytest
from unittest.mock import patch, AsyncMock
from app.core.exceptions import AppError

@pytest.mark.asyncio
async def test_login_success(client):
    """Успешный логин должен вернуть токен"""
    # ИСПРАВЛЕНО: используем AsyncMock из unittest.mock
    with patch("app.services.user_service.authenticate", new_callable=AsyncMock) as mock_auth:
        mock_auth.return_value = "fake-jwt-token-12345"
        
        response = await client.post(
            "/auth/login", 
            data={"username": "admin", "password": "secret"}
        )
        assert response.status_code == 200
        assert response.json()["access_token"] == "fake-jwt-token-12345"

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Неверный пароль должен вернуть 401"""
    with patch("app.services.user_service.authenticate", new_callable=AsyncMock) as mock_auth:
        mock_auth.side_effect = AppError("Неверный логин или пароль", "warning", 401)
        
        response = await client.post(
            "/auth/login", 
            data={"username": "admin", "password": "wrong"}
        )
        assert response.status_code == 401
        assert response.json()["result"] is False