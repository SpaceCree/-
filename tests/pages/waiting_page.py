import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.base_page import BasePage


class WaitingPage(BasePage):
    """Экран ожидания второго игрока после создания игры."""

    def __init__(self, driver: WebDriver, timeout_sec: int):
        """Инициализирует Page Object экрана ожидания."""

        super().__init__(driver, timeout_sec)

    def current_game_id(self) -> str:
        """Извлекает id игры из текущего URL."""

        match = re.search(r"/games/([^/?]+)", self.driver.current_url)
        if not match:
            self._raise_ui_error(
                action="Получение id игры из URL",
                details=f"Текущий URL не содержит id игры: {self.driver.current_url}",
            )
        return match.group(1)

    def assert_waiting_player_screen(self) -> None:
        """Проверяет, что заголовок страницы содержит 'Ожидание игрока'."""

        title = self.wait_visible(By.ID, "titleSpan").text
        if "Ожидание игрока" not in title:
            self._raise_ui_error(
                action="Проверка экрана ожидания",
                by=By.ID,
                value="titleSpan",
                details=f"Ожидали 'Ожидание игрока', фактически: '{title}'",
            )

