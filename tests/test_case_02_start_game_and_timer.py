import allure
import pytest

from tests.core.config import UiConfig
from tests.pages.battle_page import BattlePage
from tests.pages.join_page import JoinPage
from tests.pages.lobby_page import LobbyPage
from tests.pages.login_page import LoginPage
from tests.pages.waiting_page import WaitingPage


@allure.epic("Морской бой 2.0")
@allure.feature("Автоматизированные сценарии")
@allure.title("Тест кейс 2: расстановка кораблей, старт игры, выстрел и проверка таймера")
@pytest.mark.ui
def test_case_02_start_game_and_countdown(ui_config: UiConfig, driver_factory):
    driver_1 = driver_factory()
    driver_2 = driver_factory()

    login_1 = LoginPage(driver_1, ui_config.timeout_sec, ui_config.base_url)
    lobby_1 = LobbyPage(driver_1, ui_config.timeout_sec)
    waiting_1 = WaitingPage(driver_1, ui_config.timeout_sec)
    battle_1 = BattlePage(driver_1, ui_config.timeout_sec)

    login_2 = LoginPage(driver_2, ui_config.timeout_sec, ui_config.base_url)
    lobby_2 = LobbyPage(driver_2, ui_config.timeout_sec)
    join_2 = JoinPage(driver_2, ui_config.timeout_sec)
    battle_2 = BattlePage(driver_2, ui_config.timeout_sec)

    with allure.step("Игрок 1 авторизуется и создает игру"):
        login_1.open()
        login_1.login(ui_config.user1, ui_config.password1)
        lobby_1.select_game_type("Неизведанные глубины")
        lobby_1.auto_fill_ships()
        assert lobby_1.can_create_game(), "Кнопка `На абордаж!` должна быть активна после расстановки."
        lobby_1.create_game()
        game_id = waiting_1.current_game_id()
        waiting_1.assert_waiting_player_screen()
        allure.attach(game_id, "ID созданной игры", allure.attachment_type.TEXT)

    with allure.step("Игрок 2 авторизуется, расставляет корабли и входит в игру"):
        login_2.open()
        login_2.login(ui_config.user2, ui_config.password2)
        lobby_2.join_game_from_lobby(game_id)
        join_2.manual_place_10x10()
        assert join_2.can_join_game(), "Кнопка `На абордаж!` должна быть активна после расстановки."
        join_2.confirm_join_game()
        battle_2.wait_battle_screen()

    with allure.step("Игрок 1 делает выстрел, таймер не равен 00:00"):
        battle_1.wait_battle_screen()
        battle_1.wait_turn_contains(ui_config.user1)
        battle_1.fire_first_available_enemy_cell()

        countdown_value = battle_1.wait_countdown_not_zero()
        allure.attach(countdown_value, "Таймер после первого выстрела", allure.attachment_type.TEXT)
        assert countdown_value != "00:00", f"Ожидали таймер не 00:00, фактически: {countdown_value}"

