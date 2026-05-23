import re

import allure
import pytest

from tests.core.config import UiConfig
from tests.pages.lobby_page import LobbyPage
from tests.pages.login_page import LoginPage


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("ё", "е").split())


@allure.epic("Морской бой 2.0")
@allure.feature("Автоматизированные сценарии")
@allure.title("ТК-06: Проверка наличия игровых полей и правил игры `Неизведанные глубины`")
@pytest.mark.ui
def test_case_06_field_rules_unexplored_depths(ui_config: UiConfig, driver_factory):
    driver = driver_factory()

    login_page = LoginPage(driver, ui_config.timeout_sec, ui_config.base_url)
    lobby_page = LobbyPage(driver, ui_config.timeout_sec)

    with allure.step("Предусловие: авторизоваться под пользователем LuckyAlbert и открыть лобби"):
        login_page.open()
        login_page.login(ui_config.user1, ui_config.password1)

    with allure.step("Шаг 1. В блоке `Место битвы` открыть список выбора поля"):
        options = lobby_page.game_type_options()
        allure.attach("\n".join(options), "Варианты списка `Место битвы`", allure.attachment_type.TEXT)
        assert "Прибрежные воды" in options, "В списке `Место битвы` отсутствует вариант `Прибрежные воды`."
        assert "Неизведанные глубины" in options, "В списке `Место битвы` отсутствует вариант `Неизведанные глубины`."

    with allure.step("Шаг 2. Выбрать вариант `Неизведанные глубины`"):
        lobby_page.select_game_type("Неизведанные глубины")
        selected = lobby_page.selected_game_type()
        allure.attach(selected, "Выбранный вариант", allure.attachment_type.TEXT)
        assert selected == "Неизведанные глубины", (
            f"Ожидался выбранный вариант `Неизведанные глубины`, фактически: `{selected}`."
        )

    with allure.step("Шаг 3. Проверить описание времени для `Неизведанные глубины`"):
        common_desc = lobby_page.game_common_description()
        allure.attach(common_desc, "Описание времени и условий", allure.attachment_type.TEXT)
        normalized_desc = _normalize(common_desc)
        assert "время на игру" in normalized_desc, "В описании отсутствует текст про время игры."
        assert re.search(r"10\s*мин", normalized_desc), (
            "Для `Неизведанные глубины` в описании должно быть указано время 10 минут."
        )

    with allure.step("Шаг 4. Проверить описание флота"):
        fleet_desc = lobby_page.game_fleet_description()
        allure.attach(fleet_desc, "Описание флота", allure.attachment_type.TEXT)
        normalized_fleet = _normalize(fleet_desc)
        assert re.search(r"однопалубн\w*:\s*4", normalized_fleet), (
            "В описании флота должно быть `4 однопалубных`."
        )
        assert re.search(r"двухпалубн\w*:\s*2", normalized_fleet), (
            "В описании флота должно быть `2 двухпалубных`."
        )
        assert re.search(r"трехпалубн\w*:\s*1", normalized_fleet), (
            "В описании флота должно быть `1 трехпалубный`."
        )
        assert re.search(r"четырехпалубн\w*:\s*1", normalized_fleet), (
            "В описании флота должно быть `1 четырехпалубный`."
        )

    with allure.step("Шаг 5. Проверить размер сетки в блоке `Расстановка кораблей`"):
        rows, cols = lobby_page.battlefield_size()
        allure.attach(f"rows={rows}, cols={cols}", "Размер сетки", allure.attachment_type.TEXT)
        assert rows == 10, f"Ожидалось 10 строк, фактически: {rows}."
        assert cols == 10, f"Ожидалось 10 столбцов, фактически: {cols}."
