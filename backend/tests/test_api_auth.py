import pytest
from unittest.mock import patch, AsyncMock
from app.core.exceptions import AppError

@pytest.mark.asyncio
async def test_login_success(client):
    """Успешный логин должен вернуть токен"""
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

@pytest.mark.asyncio
async def test_disabled_user_cannot_login(client, mock_db_session):
    """Заблокированный пользователь получает 401"""
    from app.db.models import User
    disabled_user = User(login="banned", disabled=True)
    disabled_user.set_password("secret")
    
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = disabled_user
    
    response = await client.post("/auth/login", data={"username": "banned", "password": "secret"})
    assert response.status_code == 401