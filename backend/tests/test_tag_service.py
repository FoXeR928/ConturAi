import pytest
import uuid
from unittest.mock import AsyncMock
from app.services import tag_service
from app.db.models import Tag
from app.core.exceptions import AppError

@pytest.mark.asyncio
async def test_create_tag_duplicate(mock_db_session):
    """Нельзя создать два тега с одинаковым названием"""
    existing_tag = Tag(name="IT")
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_tag
    
    with pytest.raises(AppError) as exc:
        await tag_service.create_tag(mock_db_session, "IT", "#ff0000")
    
    assert "уже существует" in str(exc.value)
    mock_db_session.add.assert_not_called()

@pytest.mark.asyncio
async def test_create_tag_success(mock_db_session):
    """Успешное создание нового тега"""
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
    
    await tag_service.create_tag(mock_db_session, "HR", "#00ff00")
    
    mock_db_session.add.assert_called_once()
    args, _ = mock_db_session.add.call_args
    tag = args[0]
    assert tag.name == "HR"
    assert tag.color == "#00ff00"
    mock_db_session.commit.assert_called_once()