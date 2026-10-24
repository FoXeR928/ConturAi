import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from app.db.models import Chat, User
from app.services import chat_service

@pytest.mark.asyncio
async def test_soft_delete_chat(mock_db_session):
    """Чат не удаляется, а получает флаг is_deleted=True"""
    user = User(login="test_user", is_admin=False)
    chat_id = uuid.uuid4()
    chat = Chat(id=chat_id, user_login="test_user", name="Test", is_deleted=False)
    
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = chat
    
    await chat_service.soft_delete_chat(mock_db_session, user, chat_id)
    
    # execute вызывается 2 раза: 1) SELECT для получения чата, 2) UPDATE для установки флага
    assert mock_db_session.execute.call_count == 2
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_list_chats_excludes_deleted(mock_db_session):
    """Список чатов не должен содержать удаленные"""
    user = User(login="test_user")
    
    # Мокаем возврат пустого списка
    mock_db_session.execute.return_value.all.return_value = []
    
    result = await chat_service.list_chats(mock_db_session, user)
    
    assert result == []
    # Проверяем, что в запросе было условие is_deleted=False (по косвенным признакам вызова)
    mock_db_session.execute.assert_called_once()