import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.api.deps import get_current_user, get_admin_user
from app.db.session import get_session
from app.db.models import User

@pytest.fixture
def mock_user():
    return User(
        id=uuid.uuid4(), login="test_user", user_name="Тест", 
        role="user", disabled=False
    )

@pytest.fixture
def mock_admin():
    return User(
        id=uuid.uuid4(), login="admin", user_name="Админ", 
        role="admin", disabled=False
    )

@pytest.fixture
def mock_db_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    mock_result = MagicMock()
    session.execute.return_value = mock_result
    return session

@pytest.fixture
async def client(mock_db_session):
    app.dependency_overrides[get_session] = lambda: mock_db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest.fixture
async def user_client(client, mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield client

@pytest.fixture
async def admin_client(client, mock_admin):
    app.dependency_overrides[get_current_user] = lambda: mock_admin
    app.dependency_overrides[get_admin_user] = lambda: mock_admin
    yield client