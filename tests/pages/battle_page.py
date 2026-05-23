from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.base_page import BasePage
from tests.pages.base_page import UiOperationError


class BattlePage(BasePage):
    """Экран боя: ходы, выстрелы, чат и завершение игры."""

    def __init__(self, driver: WebDriver, timeout_sec: int):
        super().__init__(driver, timeout_sec)

    def wait_battle_screen(self) -> None:
        """Ожидает появление экрана боя по заголовку."""

        try:
            self.wait.until(lambda drv: "БИТВА" in drv.find_element(By.ID, "titleSpan").text)
        except Exception as exc:  # noqa: BLE001
            self._raise_ui_error(
                action="Ожидание экрана боя",
                by=By.ID,
                value="titleSpan",
                details="Заголовок не содержит 'БИТВА'",
                original_exc=exc,
            )

    def turn_text(self) -> str:
        """Возвращает текущий текст индикатора хода."""

        return self.wait_visible(By.ID, "turnSpan").text

    def fire_enemy_cell(self, row: int, col: int) -> None:
        """Выполняет выстрел по клетке поля противника."""

        locators = [
            (By.XPATH, f"//*[@id='en|b_{row}_{col}']"),
            (By.XPATH, f"//*[@id='enemy|b_{row}_{col}']"),
            (By.XPATH, f"//*[@id='enemyField']//*[contains(@id,'|b_{row}_{col}')]"),
        ]

        errors: list[str] = []
        for by, value in locators:
            try:
                self.click(by, value)
                return
            except UiOperationError as exc:
                errors.append(str(exc))

        try:
            ids_sample = self.driver.execute_script(
                "return Array.from(document.querySelectorAll('#enemyField [id]')).slice(0,40).map(e=>e.id)"
            )
        except Exception:
            ids_sample = ["<не удалось получить список id enemyField>"]

        raise UiOperationError(
            f"Не удалось кликнуть по клетке противника ({row}, {col}). "
            f"Проверенные локаторы: {locators}. Пример id в enemyField: {ids_sample}. "
            f"Ошибки попыток: {errors}"
        )

    def wait_chat_contains(self, text: str) -> None:
        """Ожидает появление подстроки в чате."""

        try:
            self.wait.until(lambda drv: text in (drv.find_element(By.ID, "chatLog").get_attribute("value") or ""))
        except Exception as exc:  # noqa: BLE001
            current_chat = self.wait_visible(By.ID, "chatLog").get_attribute("value")
            self._raise_ui_error(
                action="Ожидание текста в чате",
                by=By.ID,
                value="chatLog",
                details=f"Ожидали подстроку '{text}', фактический чат: '{current_chat}'",
                original_exc=exc,
            )

    def wait_turn_contains(self, text: str) -> None:
        """Ожидает, что индикатор хода содержит нужную подстроку."""

        try:
            self.wait.until(lambda drv: text in drv.find_element(By.ID, "turnSpan").text)
        except Exception as exc:  # noqa: BLE001
            current_turn = self.turn_text()
            self._raise_ui_error(
                action="Ожидание смены хода",
                by=By.ID,
                value="turnSpan",
                details=f"Ожидали подстроку '{text}', фактический текст хода: '{current_turn}'",
                original_exc=exc,
            )

    def chat_text(self) -> str:
        """Возвращает текущее содержимое чата."""

        return self.wait_visible(By.ID, "chatLog").get_attribute("value")

    def get_own_ships_matrix(self) -> list[list[int]]:
        """Возвращает матрицу собственного флота из JS-переменной `myShips`."""

        try:
            ships = self.driver.execute_script("return (typeof myShips !== 'undefined') ? myShips : null;")
        except Exception as exc:  # noqa: BLE001
            self._raise_ui_error(
                action="Получение матрицы собственного флота",
                details="Не удалось получить JS-переменную myShips",
                original_exc=exc,
            )

        if not ships:
            self._raise_ui_error(
                action="Получение матрицы собственного флота",
                details="JS-переменная myShips пустая или недоступна",
            )

        matrix: list[list[int]] = []
        for row in ships:
            if isinstance(row, dict) and "value" in row:
                matrix.append([int(x) for x in row["value"]])
            else:
                matrix.append([int(x) for x in row])
        return matrix

    def fire_enemy_cell_via_command(self, row: int, col: int) -> None:
        """Выполняет выстрел через JS-команду `fire(x, y)`."""

        try:
            can_fire = self.driver.execute_script("return typeof fire === 'function';")
        except Exception as exc:  # noqa: BLE001
            self._raise_ui_error(
                action="Проверка JS-функции fire",
                details="Не удалось проверить наличие функции fire(x, y)",
                original_exc=exc,
            )

        if not can_fire:
            self._raise_ui_error(
                action="Выстрел через JS-команду",
                details="На странице отсутствует функция fire(x, y)",
            )

        chat_before = self.chat_text()
        try:
            self.driver.execute_script("fire(arguments[0], arguments[1]);", int(row), int(col))
        except Exception as exc:  # noqa: BLE001
            self._raise_ui_error(
                action="Выстрел через JS-команду",
                details=f"Не удалось выполнить fire({row}, {col})",
                original_exc=exc,
            )

        try:
            self.wait.until(
                lambda drv: (
                    (drv.find_element(By.ID, "chatLog").get_attribute("value") or "") != chat_before
                    or "Побед" in drv.find_element(By.ID, "turnSpan").text
                    or "Поздравляем" in drv.find_element(By.ID, "turnSpan").text
                    or "НИЧЬЯ" in drv.find_element(By.ID, "turnSpan").text
                )
            )
        except Exception as exc:  # noqa: BLE001
            self._raise_ui_error(
                action="Ожидание результата выстрела",
                details=f"После fire({row}, {col}) чат и индикатор хода не обновились",
                original_exc=exc,
            )

    def has_winner_message(self, winner_name: str) -> bool:
        """Проверяет без ожидания, что на экране есть сообщение о победителе."""

        try:
            chat = self.driver.find_element(By.ID, "chatLog").get_attribute("value") or ""
            turn = self.driver.find_element(By.ID, "turnSpan").text or ""
        except Exception:  # noqa: BLE001
            return False

        joined = f"{turn}\n{chat}"
        checks = [
            f"{winner_name} ПОБЕЖДАЕТ",
            f"Победил(а) {winner_name}",
            f"КРаБР отправляется в {winner_name}",
        ]
        return any(check in joined for check in checks)

    def has_game_finished_message(self) -> bool:
        """Проверяет без ожидания, что игра завершена."""

        try:
            chat = self.driver.find_element(By.ID, "chatLog").get_attribute("value") or ""
            turn = self.driver.find_element(By.ID, "turnSpan").text or ""
        except Exception:  # noqa: BLE001
            return False

        joined = f"{turn}\n{chat}"
        finish_tokens = [
            "ПОБЕЖДАЕТ",
            "Победил(а)",
            "Поздравляем с победой",
            "НИЧЬЯ",
            "ВРЕМЯ ВЫШЛО",
        ]
        return any(token in joined for token in finish_tokens)

    def wait_game_finished(self) -> None:
        """Ожидает завершение игры."""

        try:
            self.wait.until(lambda drv: self.has_game_finished_message())
        except Exception as exc:  # noqa: BLE001
            self._raise_ui_error(
                action="Ожидание завершения игры",
                details=(
                    f"Игра не завершилась. Текущий turnSpan: '{self.turn_text()}'. "
                    f"Текущий chatLog: '{self.chat_text()}'"
                ),
                original_exc=exc,
            )
