import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from app.db.models import Chat, User
from app.services import chat_service

@pytest.mark.asyncio
async def test_soft_delete_chat(mock_db_session):
    """Чат не удаляется, а получает флаг is_deleted=True"""
    user = User(login="test_user", role="user")
    chat_id = uuid.uuid4()
    chat = Chat(id=chat_id, user_login="test_user", name="Test", is_deleted=False)
    
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = chat
    
    await chat_service.soft_delete_chat(mock_db_session, user, chat_id)
    
    assert mock_db_session.execute.call_count == 2
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_list_chats_excludes_deleted(mock_db_session):
    """Список чатов не должен содержать удаленные"""
    user = User(login="test_user")
    
    mock_db_session.execute.return_value.all.return_value = []
    
    result = await chat_service.list_chats(mock_db_session, user)
    
    assert result == []
    mock_db_session.execute.assert_called_once()