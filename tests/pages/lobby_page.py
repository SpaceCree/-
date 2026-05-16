from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.base_page import BasePage


class LobbyPage(BasePage):
    """Лобби: выбор конфигурации, создание игры, вход в чужую игру."""

    def __init__(self, driver: WebDriver, timeout_sec: int):
        """Инициализирует Page Object лобби."""

        super().__init__(driver, timeout_sec)

    def select_game_type(self, visible_text: str) -> None:
        """Выбирает конфигурацию игры в выпадающем списке."""

        self.select_by_visible_text(By.ID, "gameConf", visible_text)

    def auto_fill_ships(self) -> None:
        """Запускает автоматическую расстановку кораблей."""

        self.click(By.ID, "btnFill")

    def can_create_game(self) -> bool:
        """Возвращает `True`, если кнопка создания игры активна."""

        return self.is_enabled(By.ID, "btnNewGame")

    def create_game(self) -> None:
        """Нажимает кнопку создания игры."""

        self.click(By.ID, "btnNewGame")
        self.wait_visible(By.ID, "titleSpan")

    def join_game_from_lobby(self, game_id: str) -> None:
        """Из лобби переходит в форму присоединения по id игры."""

        self.click(By.XPATH, f"//*[@id='{game_id}']//*[contains(@class,'btnJoin')]")
        self.wait_url_contains(f"/games/{game_id}/join", action_name="Переход на страницу присоединения к игре")
        self.wait_visible(By.ID, "btnJoin")

