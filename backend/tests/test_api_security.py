import pytest
import uuid
from unittest.mock import patch, AsyncMock
from app.db.models import Chat

@pytest.mark.asyncio
async def test_user_cannot_access_admin_routes(user_client):
    """Обычный пользователь не должен видеть список пользователей"""
    response = await user_client.get("/users/get")
    assert response.status_code == 403
    assert response.json()["message"] == "Доступно только администратору"

@pytest.mark.asyncio
async def test_user_cannot_access_llm_configs(user_client):
    """Обычный пользователь не должен менять настройки LLM"""
    response = await user_client.get("/llm-configs/get")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_user_cannot_delete_foreign_chat(user_client, mock_db_session):
    """Пользователь не может удалить чужой чат"""
    foreign_chat_id = str(uuid.uuid4())
    
    # Мокаем БД: возвращаем чат, который принадлежит НЕ текущему юзеру
    foreign_chat = Chat(id=foreign_chat_id, user_login="other_user", name="Чужой", is_deleted=False)
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = foreign_chat
    
    response = await user_client.patch(f"/chats/delete?chat_id={foreign_chat_id}")
    
    assert response.status_code == 403
    assert response.json()["message"] == "Нет доступа"

@pytest.mark.asyncio
async def test_disabled_user_cannot_login(client, mock_db_session):
    """Заблокированный пользователь получает 401"""
    from app.db.models import User
    disabled_user = User(login="banned", disabled=True)
    disabled_user.set_password("secret")
    
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = disabled_user
    
    response = await client.post("/auth/login", data={"username": "banned", "password": "secret"})
    assert response.status_code == 401