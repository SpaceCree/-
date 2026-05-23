import re

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

from tests.pages.base_page import BasePage


class LobbyPage(BasePage):
    """Лобби: выбор конфигурации, создание игры, вход в игру."""

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
        self.wait_url_contains(
            f"/games/{game_id}/join",
            action_name="Переход на страницу присоединения к игре",
        )
        self.wait_visible(By.ID, "btnJoin")

    def game_type_options(self) -> list[str]:
        """Возвращает список вариантов из блока `Место битвы`."""

        select_el = self.wait_visible(By.ID, "gameConf")
        options = [opt.text.strip() for opt in select_el.find_elements(By.TAG_NAME, "option")]
        return [opt for opt in options if opt]

    def selected_game_type(self) -> str:
        """Возвращает выбранный вариант в блоке `Место битвы`."""

        select_el = self.wait_visible(By.ID, "gameConf")
        return Select(select_el).first_selected_option.text.strip()

    def game_common_description(self) -> str:
        """Возвращает текст описания времени и условий для выбранного поля."""

        return self.wait_visible(By.ID, "conf1DescCommon").text.strip()

    def game_fleet_description(self) -> str:
        """Возвращает текст описания состава флота выбранного поля."""

        return self.wait_visible(By.ID, "conf1DescShips").text.strip()

    def battlefield_size(self) -> tuple[int, int]:
        """Возвращает размер сетки расстановки в формате `(rows, cols)`."""

        blocks = self.driver.find_elements(
            By.XPATH,
            "//*[@id='battlefieldWrapper']//*[starts-with(@id,'bla|b_')]",
        )
        if not blocks:
            self._raise_ui_error(
                action="Определение размера сетки расстановки",
                by=By.ID,
                value="battlefieldWrapper",
                details="Не найдены клетки с id вида 'bla|b_row_col'",
            )

        row_set: set[int] = set()
        col_set: set[int] = set()
        for block in blocks:
            block_id = block.get_attribute("id") or ""
            match = re.search(r"bla\|b_(\d+)_(\d+)$", block_id)
            if not match:
                continue
            row_set.add(int(match.group(1)))
            col_set.add(int(match.group(2)))

        if not row_set or not col_set:
            self._raise_ui_error(
                action="Определение размера сетки расстановки",
                by=By.ID,
                value="battlefieldWrapper",
                details="Не удалось определить индексы строк/столбцов из id клеток",
            )

        return len(row_set), len(col_set)
