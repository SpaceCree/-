from collections.abc import Callable, Iterator

import pytest
from selenium.webdriver import Chrome

from tests.core.browser import build_driver
from tests.core.config import UiConfig


@pytest.fixture(scope="session")
def ui_config() -> UiConfig:
    """Возвращает конфигурацию UI-тестов для текущей сессии."""

    return UiConfig()


@pytest.fixture
def driver_factory(ui_config: UiConfig) -> Iterator[Callable[[], Chrome]]:

    drivers: list[Chrome] = []

    def _create_driver() -> Chrome:
        driver = build_driver(ui_config)
        drivers.append(driver)
        return driver

    yield _create_driver

    for driver in reversed(drivers):
        try:
            driver.quit()
        except Exception:  
            pass

