import pytest
import uuid
from unittest.mock import AsyncMock, patch
from app.services import user_service
from app.db.models import User
from app.core.exceptions import AppError

@pytest.mark.asyncio
async def test_cannot_delete_last_admin(mock_db_session):
    """Нельзя удалить последнего администратора"""
    admin = User(login="admin", role="admin")
    
    # Мокаем БД: пользователь существует
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = admin
    # Мокаем _admins_count: он возвращает 1 (последний)
    with patch("app.services.user_service._admins_count", new_callable=AsyncMock) as mock_count:
        mock_count.return_value = 1
        
        with pytest.raises(AppError) as exc:
            await user_service.delete_user(mock_db_session, admin, "admin")
        
        assert "Нельзя удалить последнего администратора" in str(exc.value)

@pytest.mark.asyncio
async def test_cannot_downgrade_last_admin(mock_db_session):
    """Нельзя понизить роль последнего администратора"""
    admin = User(login="admin", role="admin")
    
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = admin
    with patch("app.services.user_service._admins_count", new_callable=AsyncMock) as mock_count:
        mock_count.return_value = 1
        
        with pytest.raises(AppError) as exc:
            await user_service.update_role(mock_db_session, admin, "admin", "user")
        
        assert "Нельзя изменить роль" in str(exc.value)

@pytest.mark.asyncio
async def test_soft_delete_renames_login(mock_db_session):
    """При мягком удалении логин меняется на _deleted_..."""
    admin = User(login="admin", role="admin")
    bob = User(login="bob", role="user")
    
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = bob
    
    await user_service.delete_user(mock_db_session, admin, "bob")
    
    assert bob.disabled is True
    assert bob.login.startswith("bob_deleted_")
    mock_db_session.commit.assert_called_once()