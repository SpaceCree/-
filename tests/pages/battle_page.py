from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.pages.base_page import BasePage
from tests.pages.base_page import UiOperationError


class BattlePage(BasePage):
    """Экран боя: ходы, выстрелы, чат и проверка очереди хода."""

    def __init__(self, driver: WebDriver, timeout_sec: int):
        """Инициализирует Page Object боевого экрана."""

        super().__init__(driver, timeout_sec)

    def wait_battle_screen(self) -> None:
        """Дожидается появления заголовка экрана боя."""

        try:
            self.wait.until(lambda drv: "БИТВА" in drv.find_element(By.ID, "titleSpan").text)
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
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

    def countdown_text(self) -> str:
        """Возвращает текущее значение таймера матча."""

        return self.wait_visible(By.ID, "countdown").text.strip()

    def is_turn_of(self, player_name: str) -> bool:
        """Проверяет, что ход принадлежит указанному игроку."""

        return player_name in self.turn_text()

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
        except Exception:  # noqa: BLE001 - диагностический блок.
            ids_sample = ["<не удалось получить список id из enemyField>"]

        raise UiOperationError(
            f"Не удалось кликнуть по клетке противника ({row}, {col}). "
            f"Проверенные локаторы: {locators}. "
            f"Пример id в enemyField: {ids_sample}. "
            f"Ошибки попыток: {errors}"
        )

    def wait_chat_contains(self, text: str) -> None:
        """Ожидает появление подстроки в чате."""

        try:
            self.wait.until(lambda drv: text in (drv.find_element(By.ID, "chatLog").get_attribute("value") or ""))
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
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
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
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
        """Возвращает матрицу собственного флота текущего игрока (из JS-переменной `myShips`)."""

        try:
            ships = self.driver.execute_script("return (typeof myShips !== 'undefined') ? myShips : null;")
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
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

    def get_available_enemy_targets(self) -> list[tuple[int, int]]:
        """Возвращает список доступных для выстрела клеток поля противника."""

        try:
            targets = self.driver.execute_script(
                """
                const blocks = Array.from(document.querySelectorAll("#enemyField [id*='|b_']"));
                return blocks
                    .filter(el => el.children.length === 0 && el.childNodes.length === 0 && el.className !== 'enemyShip')
                    .map(el => {
                        const m = el.id.match(/\\|b_(\\d+)_(\\d+)/);
                        return m ? [Number(m[1]), Number(m[2])] : null;
                    })
                    .filter(Boolean);
                """
            )
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Получение доступных клеток поля противника",
                details="Не удалось прочитать состояние enemyField через executeScript",
                original_exc=exc,
            )

        return [(int(x), int(y)) for x, y in targets]

    def fire_first_available_enemy_cell(self) -> tuple[int, int]:
        """Стреляет в первую доступную клетку противника и возвращает ее координаты."""

        targets = self.get_available_enemy_targets()
        if not targets:
            raise UiOperationError("Нет доступных клеток для выстрела на поле противника.")

        row, col = targets[0]
        chat_before = self.chat_text()
        self.fire_enemy_cell(row, col)

        try:
            self.wait.until(
                lambda drv: (
                    (drv.find_element(By.ID, "chatLog").get_attribute("value") or "") != chat_before
                    or "Побед" in drv.find_element(By.ID, "turnSpan").text
                    or "Поздравляем" in drv.find_element(By.ID, "turnSpan").text
                    or "НИЧЬЯ" in drv.find_element(By.ID, "turnSpan").text
                )
            )
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Ожидание результата выстрела",
                details=f"После выстрела в ({row}, {col}) чат и индикатор хода не обновились",
                original_exc=exc,
            )

        return row, col

    def fire_enemy_cell_via_command(self, row: int, col: int) -> None:
        """Выполняет выстрел по координате через JS-команду `fire(x, y)`."""

        try:
            can_fire = self.driver.execute_script("return typeof fire === 'function';")
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Проверка JS-функции fire",
                details="Не удалось проверить наличие функции fire(x, y) на странице",
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
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
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
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Ожидание результата выстрела",
                details=f"После fire({row}, {col}) чат и индикатор хода не обновились",
                original_exc=exc,
            )

    def wait_game_finished_with_winner(self, winner_name: str) -> None:
        """Ожидает завершение игры и проверяет, что победил указанный игрок."""

        try:
            self.wait.until(lambda drv: self.has_game_finished_message())
            self.wait.until(lambda drv: self.has_winner_message(winner_name))
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Проверка победителя",
                details=(
                    f"Не найдено сообщение о победе игрока '{winner_name}'. "
                    f"Текущий turnSpan: '{self.turn_text()}'. "
                    f"Текущий chatLog: '{self.chat_text()}'"
                ),
                original_exc=exc,
            )

    def has_winner_message(self, winner_name: str) -> bool:
        """Проверяет без ожидания, что на экране есть сообщение о победе игрока."""

        try:
            chat = self.driver.find_element(By.ID, "chatLog").get_attribute("value") or ""
            turn = self.driver.find_element(By.ID, "turnSpan").text or ""
        except Exception:  # noqa: BLE001 - при переходных состояниях вернем False.
            return False

        joined = f"{turn}\n{chat}"
        checks = [
            f"{winner_name} ПОБЕЖДАЕТ",
            f"Победил(а) {winner_name}",
            f"КРаБР отправляется в {winner_name}",
        ]
        return any(check in joined for check in checks)

    def has_game_finished_message(self) -> bool:
        """Проверяет без ожидания, что игра завершена (победа или ничья)."""

        try:
            chat = self.driver.find_element(By.ID, "chatLog").get_attribute("value") or ""
            turn = self.driver.find_element(By.ID, "turnSpan").text or ""
        except Exception:  # noqa: BLE001 - переходные состояния.
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
        """Ожидает завершение игры (без проверки имени победителя)."""

        try:
            self.wait.until(lambda drv: self.has_game_finished_message())
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Ожидание завершения игры",
                details=(
                    f"Игра не завершилась. Текущий turnSpan: '{self.turn_text()}'. "
                    f"Текущий chatLog: '{self.chat_text()}'"
                ),
                original_exc=exc,
            )

    def wait_countdown_not_zero(self) -> str:
        """Ожидает запуск таймера и проверяет, что он не равен `00:00`."""

        try:
            self.wait.until(
                lambda drv: (
                    (drv.find_element(By.ID, "countdown").text or "").strip() != ""
                    and (drv.find_element(By.ID, "countdown").text or "").strip() != "00:00"
                )
            )
        except Exception as exc:  # noqa: BLE001 - единый формат UI-ошибок.
            self._raise_ui_error(
                action="Проверка таймера после выстрела",
                by=By.ID,
                value="countdown",
                details=f"Текущее значение таймера: '{self.countdown_text()}'",
                original_exc=exc,
            )

        return self.countdown_text()
