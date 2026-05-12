import allure
import pytest
from selenium.webdriver.common.by import By

from ui_helpers import GameUi, UiConfig, build_driver


@allure.epic("Морской бой 2.0")
@allure.feature("Сквозные UI сценарии")
@allure.title("Тест кейс 1: два игрока, ручная расстановка у второго, ход `мимо` у первого")
@pytest.mark.ui
def test_case_01_multiplayer_miss_flow():
    config = UiConfig()

    driver_1 = build_driver(config)
    driver_2 = build_driver(config)
    ui_1 = GameUi(driver_1, config)
    ui_2 = GameUi(driver_2, config)

    try:
        with allure.step("Блок LuckyAlbert шаг 1. Авторизация LuckyAlbert"):
            ui_1.open_start_page()
            ui_1.login(config.user1, config.password1)

        with allure.step("Блок LuckyAlbert шаг 2. Создание игры LuckyAlbert `Неизведанные глубины`"):
            ui_1.select_game_type("Неизведанные глубины")

        with allure.step("Блок LuckyAlbert шаг 3. Автоматическая расстановка кораблей по кнопке"):
            ui_1.auto_fill_ships()
            assert ui_1.is_enabled(By.ID, "btnNewGame"), "Кнопка `На абордаж!` должна стать активной после авторасстановки."

        with allure.step("Блок LuckyAlbert шаг 4. Нажатие кнопки `На абордаж!`"):
            ui_1.create_game()
            game_id = ui_1.current_game_id()
            ui_1.wait_waiting_screen()
            allure.attach(game_id, "ID созданной игры", allure.attachment_type.TEXT)

        with allure.step("Блок LuckyAlbert2 шаг 1. Авторизация LuckyAlbert2"):
            ui_2.open_start_page()
            ui_2.login(config.user2, config.password2)

        with allure.step("Блок LuckyAlbert2 шаг 2. Присоединение к игре LuckyAlbert"):
            ui_2.join_game_from_lobby(game_id)

        with allure.step("Блок LuckyAlbert2 шаг 3. Ручная расстановка кораблей"):
            ui_2.manual_place_10x10()
            assert ui_2.is_enabled(By.ID, "btnJoin"), "Кнопка `На абордаж!` должна быть активна после полной ручной расстановки."

        with allure.step("Блок LuckyAlbert2 шаг 4. Присоединение к игре"):
            ui_2.confirm_join_game()
            ui_2.wait_battle_screen()

        with allure.step("LuckyAlbert делает ход `мимо`. Тест заканчивается"):
            ui_1.wait_battle_screen()
            current_turn = ui_1.turn_text()
            allure.attach(current_turn, "Текущий ход до выстрела", allure.attachment_type.TEXT)
            assert config.user1 in current_turn, (
                f"Ожидался ход игрока {config.user1}, фактически: {current_turn}"
            )

            # Клетка enemy|b_9_9 заранее выбрана как пустая при заданной ручной расстановке игрока 2.
            ui_1.fire_enemy_cell(9, 9)
            ui_1.wait_chat_contains("Мимо")
            ui_1.wait_turn_contains(config.user2)

            chat_text = ui_1.wait_visible(By.ID, "chatLog").get_attribute("value")
            turn_after_shot = ui_1.turn_text()
            allure.attach(chat_text, "Лог чата после выстрела", allure.attachment_type.TEXT)
            allure.attach(turn_after_shot, "Текущий ход после выстрела", allure.attachment_type.TEXT)

    finally:
        driver_2.quit()
        driver_1.quit()
