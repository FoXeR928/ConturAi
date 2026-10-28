import httpx
from loguru import logger
from app.kernel import kernel
from app.kernel.contracts import BaseParser

# Имя сервиса из docker-compose.yml
OCR_SERVICE_URL = "http://ocr_service:8080"

@kernel.parser
class PDFOCRPlugin(BaseParser):
    def can_handle(self, mime_type: str, filename: str) -> bool:
        ct = (mime_type or "").lower()
        name = (filename or "").lower()
        return "pdf" in ct or name.endswith(".pdf")

    def parse(self, mime_type: str, data: bytes, filename: str = "") -> str:
        logger.info(f"Отправка '{filename}' в Sidecar-сервис OCR...")
        try:
            response = httpx.post(
                f"{OCR_SERVICE_URL}/parse",
                files={"file": (filename or "document.pdf", data, mime_type or "application/pdf")},
                timeout=300.0
            )
            response.raise_for_status()
            return response.json().get("text", "Ошибка чтения файла")
        except Exception as e:
            logger.error(f"Ошибка обращения к OCR-сервису: {e}")
            return "Ошибка чтения файла: OCR-сервис недоступен"