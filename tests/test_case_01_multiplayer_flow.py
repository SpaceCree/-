import allure
import pytest

from tests.core.config import UiConfig
from tests.pages.battle_page import BattlePage
from tests.pages.join_page import JoinPage
from tests.pages.lobby_page import LobbyPage
from tests.pages.login_page import LoginPage
from tests.pages.waiting_page import WaitingPage



###   Тест кейс 1: Победа игрока после уничтожения флота противника  ###


@allure.epic("Морской бой 2.0")
@allure.feature("Автоматизированные сценарии")
@allure.title("Тест кейс 1: Победа игрока после уничтожения флота противника")
@pytest.mark.ui
def test_case_01_multiplayer_miss_flow(ui_config: UiConfig, driver_factory):
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

    with allure.step("Блок LuckyAlbert шаг 1. Авторизация LuckyAlbert"):
        login_1.open()
        login_1.login(ui_config.user1, ui_config.password1)

    with allure.step("Блок LuckyAlbert шаг 2. Создание игры LuckyAlbert `Неизведанные глубины`"):
        lobby_1.select_game_type("Неизведанные глубины")

    with allure.step("Блок LuckyAlbert шаг 3. Автоматическая расстановка кораблей по кнопке"):
        lobby_1.auto_fill_ships()
        assert lobby_1.can_create_game(), "Кнопка `На абордаж!` должна стать активной после авторасстановки."

    with allure.step("Блок LuckyAlbert шаг 4. Нажатие кнопки `На абордаж!`"):
        lobby_1.create_game()
        game_id = waiting_1.current_game_id()
        waiting_1.assert_waiting_player_screen()
        allure.attach(game_id, "ID созданной игры", allure.attachment_type.TEXT)

    with allure.step("Блок LuckyAlbert2 шаг 1. Авторизация LuckyAlbert2"):
        login_2.open()
        login_2.login(ui_config.user2, ui_config.password2)

    with allure.step("Блок LuckyAlbert2 шаг 2. Присоединение к игре LuckyAlbert"):
        lobby_2.join_game_from_lobby(game_id)

    with allure.step("Блок LuckyAlbert2 шаг 3. Ручная расстановка кораблей"):
        join_2.manual_place_10x10()
        assert join_2.can_join_game(), "Кнопка `На абордаж!` должна быть активна после полной ручной расстановки."

    with allure.step("Блок LuckyAlbert2 шаг 4. Присоединение к игре"):
        join_2.confirm_join_game()
        battle_2.wait_battle_screen()

    with allure.step("LuckyAlbert делает ход `мимо`. Тест заканчивается"):
        battle_1.wait_battle_screen()
        current_turn = battle_1.turn_text()
        allure.attach(current_turn, "Текущий ход до выстрела", allure.attachment_type.TEXT)
        assert ui_config.user1 in current_turn, (
            f"Ожидался ход игрока {ui_config.user1}, фактически: {current_turn}"
        )

        battle_1.fire_enemy_cell(9, 9)
        battle_1.wait_chat_contains("Мимо")
        battle_1.wait_turn_contains(ui_config.user2)

        chat_text = battle_1.chat_text()
        turn_after_shot = battle_1.turn_text()
        allure.attach(chat_text, "Лог чата после выстрела", allure.attachment_type.TEXT)
        allure.attach(turn_after_shot, "Текущий ход после выстрела", allure.attachment_type.TEXT)

    with allure.step("LuckyAlbert2 разрушает все корабли и выигрывает"):
        # Матрицу флота LuckyAlbert знаем из его окна.
        # LuckyAlbert2 бьет именно по палубам, чтобы гарантированно завершить игру победой.
        player1_matrix = battle_1.get_own_ships_matrix()
        player1_ship_targets = [
            (row, col)
            for row in range(len(player1_matrix))
            for col in range(len(player1_matrix[row]))
            if int(player1_matrix[row][col]) > 0
        ]
        assert player1_ship_targets, "Не удалось получить палубы LuckyAlbert из матрицы myShips."

        for row, col in player1_ship_targets:
            if battle_2.has_winner_message(ui_config.user2):
                break
            battle_2.wait_turn_contains(ui_config.user2)
            battle_2.fire_enemy_cell_via_command(row, col)

        battle_1.wait_game_finished()
        battle_2.wait_game_finished()

        chat_1 = battle_1.chat_text()
        chat_2 = battle_2.chat_text()
        turn_1 = battle_1.turn_text()
        turn_2 = battle_2.turn_text()
        allure.attach(chat_1, "Чат после завершения игры (окно LuckyAlbert)", allure.attachment_type.TEXT)
        allure.attach(chat_2, "Чат после завершения игры (окно LuckyAlbert2)", allure.attachment_type.TEXT)
        allure.attach(turn_1, "Индикатор хода после завершения (окно LuckyAlbert)", allure.attachment_type.TEXT)
        allure.attach(turn_2, "Индикатор хода после завершения (окно LuckyAlbert2)", allure.attachment_type.TEXT)

        assert battle_1.has_winner_message(ui_config.user2), (
            f"В окне LuckyAlbert победителем указан не {ui_config.user2}. "
            f"turnSpan='{turn_1}'."
        )
        assert battle_2.has_winner_message(ui_config.user2), (
            f"В окне LuckyAlbert2 победителем указан не {ui_config.user2}. "
            f"turnSpan='{turn_2}'."
        )
