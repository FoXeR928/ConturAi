import pytest
import uuid
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_create_chat(user_client):
    """Создание чата возвращает UUID"""
    new_chat_id = str(uuid.uuid4())
    
    # ИСПРАВЛЕНО: используем AsyncMock из unittest.mock
    with patch("app.services.chat_service.create_chat", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = new_chat_id
        
        response = await user_client.post("/chats/create", json={"name": "Новый тестовый чат"})
        assert response.status_code == 200
        assert response.json()["chat_id"] == new_chat_id

@pytest.mark.asyncio
async def test_get_chats(user_client):
    """Получение списка чатов"""
    chats = [{"id": str(uuid.uuid4()), "name": "Чат 1"}]
    
    with patch("app.services.chat_service.list_chats", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = chats
        
        response = await user_client.get("/chats/get")
        assert response.status_code == 200
        assert len(response.json()["chats"]) == 1
        assert response.json()["chats"][0]["name"] == "Чат 1"