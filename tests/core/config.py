import os
from dataclasses import dataclass


@dataclass(frozen=True)
class UiConfig:
    """Конфигурация UI-тестов, считываемая из переменных окружения."""

    base_url: str = os.getenv("BASE_URL", "http://isador.ru:8080/")
    user1: str = os.getenv("USER1", "LuckyAlbert")
    password1: str = os.getenv("PASSWORD1", "123")
    user2: str = os.getenv("USER2", "LuckyAlbert2")
    password2: str = os.getenv("PASSWORD2", "123")
    timeout_sec: int = int(os.getenv("UI_TIMEOUT_SEC", "20"))
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"
    browser_size: str = os.getenv("BROWSER_SIZE", "1920,1080")
