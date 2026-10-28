import pytest
from unittest.mock import patch, MagicMock
from app.services import system_service

@pytest.mark.asyncio
async def test_get_system_stats(admin_client, mock_db_session):
    """Проверка получения метрик мониторинга"""
    # Мокаем сбор "железных" метрик
    with patch("app.services.system_service.get_system_stats") as mock_hw:
        mock_hw.return_value = {
            "cpu": {"percent": 10, "cores": 8},
            "ram": {"total": 100, "used": 50, "percent": 50},
            "gpus": []
        }
        
        # Мокаем метрики LLM (запрос к БД)
        mock_db_session.execute.return_value.one.return_value = (10, 100, 200, 5000)
        
        response = await admin_client.get("/system/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["stats"]["cpu"]["percent"] == 10
        assert "llm_stats" in data

@pytest.mark.asyncio
async def test_list_backups_empty(admin_client, tmp_path):
    """Проверка, что список бэкапов возвращается (пусть и пустой)"""
    # Мокаем папку с бэкапами, чтобы тест не зависел от файловой системы
    with patch("app.api.v1.system.BACKUP_DIR", tmp_path):
        with patch("app.api.v1.system.subprocess.run") as mock_subprocess:
            # Мокаем ответ psql о размере БД
            mock_result = MagicMock()
            mock_result.stdout = "102400"
            mock_subprocess.return_value = mock_result
            
            response = await admin_client.get("/system/db/backups")
            
            assert response.status_code == 200
            data = response.json()
            assert data["backups"] == []
            assert data["db_size"] == 102400