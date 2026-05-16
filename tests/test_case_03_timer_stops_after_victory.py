import time

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
@allure.title("Тест кейс 3: после победы таймер останавливается")
@pytest.mark.ui
def test_case_03_timer_stops_after_victory(ui_config: UiConfig, driver_factory):
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

    with allure.step("Игрок 1 создает игру"):
        login_1.open()
        login_1.login(ui_config.user1, ui_config.password1)
        lobby_1.select_game_type("Неизведанные глубины")
        lobby_1.auto_fill_ships()
        assert lobby_1.can_create_game(), "Кнопка `На абордаж!` должна быть активна после авторасстановки."
        lobby_1.create_game()
        game_id = waiting_1.current_game_id()
        waiting_1.assert_waiting_player_screen()
        allure.attach(game_id, "ID созданной игры", allure.attachment_type.TEXT)

    with allure.step("Игрок 2 присоединяется расставляет корабли"):
        login_2.open()
        login_2.login(ui_config.user2, ui_config.password2)
        lobby_2.join_game_from_lobby(game_id)
        lobby_2.auto_fill_ships()
        assert join_2.can_join_game(), "Кнопка `На абордаж!` должна быть активна после расстановки."
        join_2.confirm_join_game()
        battle_2.wait_battle_screen()

    with allure.step("Игрок 1 делает первый выстрел (мимо), таймер запускается"):
        battle_1.wait_battle_screen()
        battle_1.wait_turn_contains(ui_config.user1)
        battle_1.fire_enemy_cell(9, 9)
        battle_1.wait_chat_contains("Мимо")
        battle_1.wait_turn_contains(ui_config.user2)
        started_countdown = battle_1.wait_countdown_not_zero()
        allure.attach(started_countdown, "Таймер после старта матча", allure.attachment_type.TEXT)

    with allure.step("Игрок 2 добивает флот игрока 1 до завершения игры"):
        player1_matrix = battle_1.get_own_ships_matrix()
        player1_ship_targets = [
            (row, col)
            for row in range(len(player1_matrix))
            for col in range(len(player1_matrix[row]))
            if int(player1_matrix[row][col]) > 0
        ]
        assert player1_ship_targets, "Не удалось получить координаты кораблей игрока 1."

        for row, col in player1_ship_targets:
            if battle_2.has_game_finished_message():
                break
            battle_2.wait_turn_contains(ui_config.user2)
            battle_2.fire_enemy_cell_via_command(row, col)

        battle_1.wait_game_finished()
        battle_2.wait_game_finished()

    with allure.step("Проверка: после победы таймер не изменяется"):
        countdown_before = battle_1.countdown_text()
        time.sleep(3)
        countdown_after = battle_1.countdown_text()

        allure.attach(countdown_before, "Таймер сразу после завершения", allure.attachment_type.TEXT)
        allure.attach(countdown_after, "Таймер через 3 секунды", allure.attachment_type.TEXT)

        assert countdown_before == countdown_after, (
            f"Ожидали остановку таймера после победы, но значение изменилось: "
            f"{countdown_before} -> {countdown_after}"
        )
