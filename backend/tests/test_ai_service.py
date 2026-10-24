import pytest
import uuid
from unittest.mock import patch, AsyncMock
from app.services.ai_service import ask
from app.db.models import Chat, User

@pytest.mark.asyncio
async def test_ask_ai_success(mock_db_session):
    """Проверяем, что ИИ получает контекст и сохраняет ответ"""
    user = User(login="test_user", is_admin=False)
    chat_id = uuid.uuid4()
    
    # Мокаем поиск чата
    chat = Chat(id=chat_id, user_login="test_user", name="Test", is_deleted=False)
    mock_db_session.execute.return_value.scalar_one_or_none.return_value = chat
    
    # Мокаем поиск документов (RAG)
    with patch("app.services.ai_service.search_documents", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []
        
        # Мокаем получение промтов
        with patch("app.services.prompt_service.get_all_prompts", new_callable=AsyncMock) as mock_prompts:
            mock_prompts.return_value = {"ai_name": "Контур", "system_prompt": "{context}", "user_prompt": "{quest}"}
            
            # Мокаем сам запрос к LLM
            with patch("app.services.ai_service._chat_completion", new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = "Это тестовый ответ от нейросети."
                
                result = await ask(mock_db_session, user, chat_id, "Привет")
                
                # ИСПРАВЛЕНО: теперь строка точно совпадает
                assert result == "Это тестовый ответ от нейросети."
                assert mock_db_session.add.call_count == 2
                assert mock_db_session.commit.called