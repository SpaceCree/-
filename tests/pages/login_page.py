from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.base_page import BasePage


class LoginPage(BasePage):
    """Стартовая страница с авторизацией."""

    def __init__(self, driver: WebDriver, timeout_sec: int, base_url: str):
        """Инициализирует страницу авторизации и базовый URL."""

        super().__init__(driver, timeout_sec)
        self.base_url = base_url

    def open(self) -> None:
        """Открывает стартовую страницу и ждет поле логина."""

        try:
            self.driver.get(self.base_url)
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Открытие стартовой страницы",
                details=f"Не удалось открыть URL: {self.base_url}",
                original_exc=exc,
            )
        self.wait_visible(By.ID, "username")

    def login(self, username: str, password: str) -> None:
        """Авторизует пользователя и дожидается открытия лобби."""

        self.type_text(By.ID, "username", username)
        self.type_text(By.ID, "password", password)
        self.click(By.ID, "loginBtn")
        self.wait_visible(By.ID, "gameConf")

