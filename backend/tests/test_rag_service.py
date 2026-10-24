import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock
from app.rag import add_document, search_documents
from app.db.models import Document

@pytest.mark.asyncio
async def test_add_document(mock_db_session):
    """Проверка нарезки и сохранения документа"""
    text = "А" * 500 + "\n\n" + "Б" * 500
    
    # Мокаем получение настроек RAG из БД
    with patch("app.services.llm_config_service.get_rag", new_callable=AsyncMock) as mock_rag:
        mock_rag.return_value = {"chunk_size": 600, "chunk_overlap": 50, "batch_size": 10}
        
        # Мокаем эмбеддинги, чтобы не грузить модель
        with patch("app.rag.embed_texts", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [[0.1] * 1024] * 2  # Возвращаем 2 вектора
            
            count = await add_document(mock_db_session, "test.pdf", text)
            
            assert count == 2
            # Проверяем, что add_all был вызван с объектами Document
            mock_db_session.add_all.assert_called_once()
            args, _ = mock_db_session.add_all.call_args
            points = args[0]
            assert len(points) == 2
            assert isinstance(points[0], Document)
            assert points[0].source == "test.pdf"

@pytest.mark.asyncio
async def test_search_documents(mock_db_session):
    """Проверка поиска документов"""
    query = "тестовый запрос"
    
    with patch("app.services.llm_config_service.get_rag", new_callable=AsyncMock) as mock_rag:
        mock_rag.return_value = {"search_limit": 5}
        
        with patch("app.rag.embed_one", new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1024
            
            # Мокаем возврат из БД
            mock_doc = Document(source="doc.pdf", text="Найденный текст")
            mock_db_session.execute.return_value.scalars.return_value.all.return_value = [mock_doc]
            
            result = await search_documents(mock_db_session, query)
            
            assert len(result) == 1
            assert result[0].text == "Найденный текст"