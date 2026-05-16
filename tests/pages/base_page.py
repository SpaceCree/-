try:
    import allure
except Exception:  # noqa: BLE001 - Allure в хелпере опционален.
    allure = None

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    InvalidElementStateException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import Select, WebDriverWait


class UiOperationError(AssertionError):
    """заворачивать конкретную ошибку"""


class BasePage:
    """Базовый класс Page Object с общими UI-операциями и обработкой ошибок."""

    def __init__(self, driver: WebDriver, timeout_sec: int):
        """Инициализирует страницу с драйвером и ожиданиями."""

        self.driver = driver
        self.timeout_sec = timeout_sec
        self.wait = WebDriverWait(driver, timeout_sec)

    def wait_visible(self, by: str, value: str):
        """Возвращает элемент после ожидания его видимости."""

        try:
            return self.wait.until(
                lambda drv: self._find_visible_element(drv, by, value)
            )
        except TimeoutException as exc:
            self._raise_ui_error(
                action="Ожидание видимого элемента",
                by=by,
                value=value,
                details="Элемент не найден или не стал видимым за отведенное время",
                original_exc=exc,
            )

    def wait_clickable(self, by: str, value: str):
        """Возвращает элемент после ожидания его кликабельности."""

        try:
            return self.wait.until(
                lambda drv: self._find_clickable_element(drv, by, value)
            )
        except TimeoutException as exc:
            self._raise_ui_error(
                action="Ожидание кликабельного элемента",
                by=by,
                value=value,
                details="Элемент не найден или не стал кликабельным за отведенное время",
                original_exc=exc,
            )

    def click(self, by: str, value: str) -> None:
        """Кликает по кликабельному элементу."""

        last_exc: Exception | None = None
        for _ in range(2):
            element = self.wait_clickable(by, value)
            try:
                element.click()
                return
            except StaleElementReferenceException as exc:
                last_exc = exc
                continue
            except (ElementClickInterceptedException, WebDriverException) as exc:
                last_exc = exc
                break

        self._raise_ui_error(
            action="Клик по элементу",
            by=by,
            value=value,
            details="Элемент перекрыт, устарел или временно недоступен для клика",
            original_exc=last_exc,
        )

    def type_text(self, by: str, value: str, text: str) -> None:
        """Очищает поле и вводит в него переданный текст."""

        element = self.wait_visible(by, value)
        try:
            element.clear()
            element.send_keys(text)
        except (InvalidElementStateException, StaleElementReferenceException, WebDriverException) as exc:
            self._raise_ui_error(
                action="Ввод текста",
                by=by,
                value=value,
                details=f"Не удалось ввести текст длиной {len(text)} символов",
                original_exc=exc,
            )

    def select_by_visible_text(self, by: str, value: str, visible_text: str) -> None:
        """Выбирает опцию в `select` по видимому тексту."""

        element = self.wait_visible(by, value)
        select = Select(element)
        try:
            select.select_by_visible_text(visible_text)
        except NoSuchElementException as exc:
            self._raise_ui_error(
                action="Выбор значения в списке",
                by=by,
                value=value,
                details=f"Не найден вариант '{visible_text}'",
                original_exc=exc,
            )

    def wait_url_contains(self, url_part: str, action_name: str) -> None:
        """Ожидает, что текущий URL содержит заданную подстроку."""

        try:
            self.wait.until(ec.url_contains(url_part))
        except TimeoutException as exc:
            self._raise_ui_error(
                action=action_name,
                details=f"Текущий URL не содержит '{url_part}'",
                original_exc=exc,
            )

    def is_enabled(self, by: str, value: str) -> bool:
        """Проверяет, что у элемента отсутствует атрибут `disabled`."""

        element = self.wait_visible(by, value)
        return element.get_attribute("disabled") is None

    def _raise_ui_error(
        self,
        action: str,
        by: str | None = None,
        value: str | None = None,
        details: str | None = None,
        original_exc: Exception | None = None,
    ) -> None:
        locator_part = f" | Локатор: ({by}, {value})" if by is not None and value is not None else ""
        message = (
            f"{action} не выполнено.{locator_part}"
            f" | URL: {self._safe_current_url()}"
            f" | Title: {self._safe_title()}"
            f" | Timeout: {self.timeout_sec} сек."
        )
        if details:
            message += f" | Детали: {details}"
        if original_exc:
            message += f" | Причина: {original_exc.__class__.__name__}: {original_exc}"

        self._attach_screenshot(name=f"Ошибка UI: {action}")
        raise UiOperationError(message) from original_exc

    def _safe_current_url(self) -> str:
        try:
            return self.driver.current_url
        except WebDriverException:
            return "<url недоступен>"

    def _safe_title(self) -> str:
        try:
            return self.driver.title
        except WebDriverException:
            return "<title недоступен>"

    def _find_visible_element(self, drv, by: str, value: str):
        try:
            element = drv.find_element(by, value)
            return element if element.is_displayed() else False
        except (NoSuchElementException, StaleElementReferenceException):
            return False

    def _find_clickable_element(self, drv, by: str, value: str):
        try:
            element = drv.find_element(by, value)
            return element if element.is_displayed() and element.is_enabled() else False
        except (NoSuchElementException, StaleElementReferenceException):
            return False

    def _attach_screenshot(self, name: str) -> None:
        if allure is None:
            return
        try:
            allure.attach(self.driver.get_screenshot_as_png(), name, allure.attachment_type.PNG)
        except WebDriverException:
            pass
