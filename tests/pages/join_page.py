from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.base_page import BasePage


class JoinPage(BasePage):
    """Страница расстановки флота перед входом в игру."""

    def __init__(self, driver: WebDriver, timeout_sec: int):

        super().__init__(driver, timeout_sec)

    def place_ship_drag(self, start_row: int, start_col: int, end_row: int, end_col: int) -> None:
        """Ставит корабль перетаскиванием от стартовой до конечной клетки."""

        start = self.wait_visible(By.XPATH, f"//*[@id='bla|b_{start_row}_{start_col}']")
        end = self.wait_visible(By.XPATH, f"//*[@id='bla|b_{end_row}_{end_col}']")
        try:
            ActionChains(self.driver).move_to_element(start).click_and_hold(start).move_to_element(end).release(end).perform()
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Drag-and-drop корабля",
                details=f"Не удалось перетащить корабль из ({start_row}, {start_col}) в ({end_row}, {end_col})",
                original_exc=exc,
            )

    def manual_place_10x10(self) -> None:
        """Выполняет подготовленную ручную расстановку для поля 10x10."""

        placements = [
            (0, 0, 0, 3),
            (2, 0, 2, 2),
            (4, 0, 5, 0),
            (4, 2, 5, 2),
            (7, 0, 7, 0),
            (7, 2, 7, 2),
            (9, 0, 9, 0),
            (9, 2, 9, 2),
        ]
        for start_row, start_col, end_row, end_col in placements:
            self.place_ship_drag(start_row, start_col, end_row, end_col)

    def can_join_game(self) -> bool:
        """Возвращает `True`, если кнопка входа в игру активна."""

        return self.is_enabled(By.ID, "btnJoin")

    def confirm_join_game(self) -> None:
        """Подтверждает вход в игру после расстановки флота."""

        self.click(By.ID, "btnJoin")
        self.wait_url_contains("/games/", action_name="Ожидание перехода в игру после присоединения")
        self.wait_visible(By.ID, "titleSpan")

