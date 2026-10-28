import pytest
from unittest.mock import MagicMock
from app.services import audit_service
from app.db.models import AuditLog

@pytest.mark.asyncio
async def test_log_action_success(mock_db_session):
    """Проверяем, что запись лога вызывается с правильными данными"""
    await audit_service.log_action(
        mock_db_session, 
        user_login="test", 
        action="upload_doc", 
        details="file.pdf", 
        ip_address="127.0.0.1"
    )
    
    mock_db_session.add.assert_called_once()
    args, _ = mock_db_session.add.call_args
    log = args[0]
    
    assert isinstance(log, AuditLog)
    assert log.user_login == "test"
    assert log.action == "upload_doc"
    assert log.ip_address == "127.0.0.1"
    mock_db_session.commit.assert_called_once()

@pytest.mark.asyncio
async def test_log_action_does_not_crash_on_error(mock_db_session):
    """Ошибка записи лога не должна ломать работу сервиса"""
    # Заставляем метод add выбросить исключение
    mock_db_session.add.side_effect = Exception("DB Error")
    
    # Не должно быть исключения наружу
    await audit_service.log_action(mock_db_session, "test", "action")
    
    # Убеждаемся, что commit не был вызван
    mock_db_session.commit.assert_not_called()