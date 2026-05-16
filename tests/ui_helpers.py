import os
import re
from dataclasses import dataclass

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait


@dataclass
class UiConfig:
    """Конфигурация UI-тестов, считываемая из переменных окружения. Вместо env"""

    base_url: str = os.getenv("BASE_URL", "http://isador.ru:8080/")
    user1: str = os.getenv("USER1", "LuckyAlbert")
    password1: str = os.getenv("PASSWORD1", "123")
    user2: str = os.getenv("USER2", "LuckyAlbert2")
    password2: str = os.getenv("PASSWORD2", "123")
    timeout_sec: int = int(os.getenv("UI_TIMEOUT_SEC", "20"))
    headless: bool = os.getenv("HEADLESS", "false").lower() == "true"
    browser_size: str = os.getenv("BROWSER_SIZE", "1920,1080")


def build_driver(config: UiConfig) -> Chrome:
    """Создает и настраивает экземпляр Chrome WebDriver."""

    options = Options()
    if config.headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=" + config.browser_size)
    options.add_argument("--lang=ru-RU")
    return Chrome(options=options)

#Завернули в класс над страницами чтобы было удобно писать логи
class GameUi:

    #Инициализирует помощник с драйвером, конфигом и WebDriverWait.
    def __init__(self, driver: Chrome, config: UiConfig):
        self.driver = driver
        self.config = config
        self.wait = WebDriverWait(driver, config.timeout_sec)

    #Открывает стартовую страницу и ждет поле логина.
    def open_start_page(self) -> None:
        self.driver.get(self.config.base_url)
        self.wait_visible(By.ID, "username")

    #Авторизует пользователя по логину и паролю
    def login(self, username: str, password: str) -> None:
        self.type_text(By.ID, "username", username)
        self.type_text(By.ID, "password", password)
        self.click(By.ID, "loginBtn")
        self.wait_visible(By.ID, "gameConf")

    #Выбирает конфигурацию игры в выпадающем списке.
    def select_game_type(self, visible_text: str) -> None:
        select = Select(self.wait_visible(By.ID, "gameConf"))
        select.select_by_visible_text(visible_text)

    #Запускает автоматическую расстановку кораблей.
    def auto_fill_ships(self) -> None:
        self.click(By.ID, "btnFill")

    #Проверяет, что элемент не имеет атрибута `disabled`. То есть элемеент виден
    def is_enabled(self, by: By, value: str) -> bool:
        element = self.wait_visible(by, value)
        return element.get_attribute("disabled") is None

    # Нажимает кнопку новая игра и дожидается экрана ожидания/подтверждения.
    def create_game(self) -> None:
        self.click(By.ID, "btnNewGame")
        self.wait_visible(By.ID, "titleSpan")

    #Извлекает id игры из текущего URL.
    def current_game_id(self) -> str:
        match = re.search(r"/games/([^/?]+)", self.driver.current_url)
        if not match:
            raise AssertionError(f"Не удалось получить id игры из URL: {self.driver.current_url}")
        return match.group(1)

    #Проверяет, что открыт экран ожидания второго игрока.
    def wait_waiting_screen(self) -> None:
        title = self.wait_visible(By.ID, "titleSpan").text
        if "Ожидание игрока" not in title:
            raise AssertionError(f"Ожидался экран ожидания, фактический заголовок: {title}")
    
    #Присоединяется к игре из лобби по id игры. По сути жмет кнопку присоединиться.
    def join_game_from_lobby(self, game_id: str) -> None:
        self.wait_clickable(By.XPATH, f"//*[@id='{game_id}']//*[contains(@class,'btnJoin')]").click()
        self.wait.until(ec.url_contains(f"/games/{game_id}/join"))
        self.wait_visible(By.ID, "btnJoin")

    #Растановка кораблей. Начальная и конечная координата
    def place_ship_drag(self, start_row: int, start_col: int, end_row: int, end_col: int) -> None:
        start = self.wait_visible(By.XPATH, f"//*[@id='bla|b_{start_row}_{start_col}']")
        end = self.wait_visible(By.XPATH, f"//*[@id='bla|b_{end_row}_{end_col}']")
        ActionChains(self.driver).move_to_element(start).click_and_hold(start).move_to_element(end).release(end).perform()


    #Ручная растановка кораблей. 10х10
    def manual_place_10x10(self) -> None:
        placements = [
            (0, 0, 0, 3),  # 4-палубный
            (2, 0, 2, 2),  # 3-палубный
            (4, 0, 5, 0),  # 2-палубный
            (4, 2, 5, 2),  # 2-палубный
            (7, 0, 7, 0),  # 1-палубный
            (7, 2, 7, 2),  # 1-палубный
            (9, 0, 9, 0),  # 1-палубный
            (9, 2, 9, 2),  # 1-палубный
        ]
        for start_row, start_col, end_row, end_col in placements:
            self.place_ship_drag(start_row, start_col, end_row, end_col)

    #Подтверждает вход в игру после расстановки флота
    def confirm_join_game(self) -> None:
        self.click(By.ID, "btnJoin")
        self.wait.until(ec.url_contains("/games/"))
        self.wait_visible(By.ID, "titleSpan")

    #Дожидается появления заголовка экрана боя.
    def wait_battle_screen(self) -> None:
        self.wait.until(lambda drv: "БИТВА" in drv.find_element(By.ID, "titleSpan").text)

    #Возвращает текущий текст индикатора хода.
    def turn_text(self) -> str:
        return self.wait_visible(By.ID, "turnSpan").text

    #Выстрел по клетке противника
    def fire_enemy_cell(self, row: int, col: int) -> None:
        # На экране боя поле противника может иметь разные префиксы id:
        # en|b_<row>_<col> или enemy|b_<row>_<col> в зависимости от версии фронта.
        locators = [
            (By.XPATH, f"//*[@id='en|b_{row}_{col}']"),
            (By.XPATH, f"//*[@id='enemy|b_{row}_{col}']"),
            (By.XPATH, f"//*[@id='enemyField']//*[contains(@id,'|b_{row}_{col}')]"),
        ]

        last_error = None
        for by, value in locators:
            try:
                self.wait_clickable(by, value).click()
                return
            except Exception as exc: 
                last_error = exc

        ids_sample = self.driver.execute_script(
            "return Array.from(document.querySelectorAll('#enemyField [id]')).slice(0,40).map(e=>e.id)"
        )
        raise AssertionError(
            f"Не удалось кликнуть по клетке противника ({row}, {col}). "
            f"Проверенные локаторы: {locators}. Пример id в enemyField: {ids_sample}"
        ) from last_error

    #Ожидание текста в чате
    def wait_chat_contains(self, text: str) -> None:
        self.wait.until(lambda drv: text in drv.find_element(By.ID, "chatLog").get_attribute("value"))

    #Ожидает, что индикатор хода содержит нужную подстроку.
    def wait_turn_contains(self, text: str) -> None:
        self.wait.until(lambda drv: text in drv.find_element(By.ID, "turnSpan").text)

    #Клик 2.0. Проверяет на кликабельность.
    def click(self, by: By, value: str) -> None:
        """Кликает по кликабельному элементу."""

        self.wait_clickable(by, value).click()

    #Очищает поле ввода и вводит в него текст
    def type_text(self, by: By, value: str, text: str) -> None:
        element = self.wait_visible(by, value)
        element.clear()
        element.send_keys(text)

    #Ожидание появление элемента
    def wait_visible(self, by: By, value: str):
        return self.wait.until(ec.visibility_of_element_located((by, value)))

    #Ждет кликабельности элемента
    def wait_clickable(self, by: By, value: str):
        return self.wait.until(ec.element_to_be_clickable((by, value)))
