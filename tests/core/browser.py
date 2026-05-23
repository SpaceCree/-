from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options

from tests.core.config import UiConfig


def build_driver(config: UiConfig) -> Chrome:
    """Создает и настраивает экземпляр Chrome WebDriver."""

    options = Options()
    if config.headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=" + config.browser_size)
    options.add_argument("--lang=ru-RU")
    return Chrome(options=options)
