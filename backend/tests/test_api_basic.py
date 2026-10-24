import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    """Сервер должен отвечать 200 OK на /status"""
    response = await client.get("/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Без токена защищенные эндпоинты должны возвращать 401"""
    response = await client.get("/chats/get")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_access_denied(user_client):
    """Обычный пользователь не должен попасть в админку (403)"""
    response = await user_client.get("/users/get")
    assert response.status_code == 403