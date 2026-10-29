class AppError(Exception):
    """
    Кастомное исключение для всего приложения.
    Позволяет возвращать клиенту понятный JSON с ошибкой.
    """
    def __init__(
        self,
        message: str,
        category: str = "error",  # "error" (красный) или "warning" (желтый)
        status_code: int = 500,
        result: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.category = category
        self.status_code = status_code
        self.result = result