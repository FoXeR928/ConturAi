# ==============================================================================
# БЛОК 1: ОПРЕДЕЛЕНИЕ КАСТОМНОГО ИСКЛЮЧЕНИЯ (CUSTOM EXCEPTION)
# ==============================================================================

class AppError(Exception):
    """
    Кастомное исключение для всего приложения.
    
    Зачем оно нужно, если есть стандартный HTTPException?
    1. Единый формат ответа: FastAPI автоматически перехватывает это исключение 
       (через @app.exception_handler(AppError) в main.py) и возвращает JSON 
       строго определенного формата: {"result": False, "message": "...", "category": "..."}.
    2. Удобство для фронтенда: фронтенд всегда знает, что ошибка будет содержать 
       поле `message` (для показа пользователю) и `category` (чтобы выбрать цвет тоста: 
       красный для "error", желтый для "warning").
    3. Меньше boilerplate-кода: в бизнес-логике (сервисах) мы просто пишем 
       `raise AppError("Ошибка", "warning", 404)`, не заботясь о JSONResponse.
    """
    
    def __init__(
        self,
        message: str,             # Текст ошибки (показывается пользователю)
        category: str = "error",  # Категория: "error" (красный) или "warning" (желтый)
        status_code: int = 500,   # HTTP-статус (по умолчанию 500 Internal Server Error)
        result: bool = False,     # Флаг успеха операции (всегда False для ошибок)
    ) -> None:
        # Вызываем родительский __init__ (от Exception), чтобы сохранить message 
        # в стандартном атрибуте `args`, это полезно для логов и трейсинга (traceback).
        super().__init__(message)
        
        # Сохраняем параметры как атрибуты экземпляра. 
        # Это позволяет обработчику исключений в main.py прочитать их:
        # exc.message, exc.category, exc.status_code, exc.result.
        self.message = message
        self.category = category
        self.status_code = status_code
        self.result = result