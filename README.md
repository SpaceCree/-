# UI автотесты (Python + Selenium + Pytest + Allure)

## 1) Создание окружения
в терминале:
python -m venv venv
.\venv\Scripts\Activate


## 2) Установка зависимостей
pip install -r requirements.txt

## 3) Запуск тестов
Запуск всех тестов:
pytest
ИЛИ
Запуск конкретного теста:
pytest tests\{название теста}
Например:
pytest tests\test_case_02_start_game_and_timer.

Настройка параметров
Запуск с открытым браузером:
$env:HEADLESS="false"
pytest


Запуск в headless-режиме: (без оконный режим)
$env:HEADLESS="true"
pytest

## 4) Просмотр Allure отчета. -> Это уже прописано в мета классе UiConfig в файле config.py
1. Запустить тесты с сохранением результатов:
pytest --alluredir=allure-results

2. Открыть отчет (без установки через Chocolatey):

npx -y allure-commandline serve allure-results

Либо отдельно собрать и открыть:


npx -y allure-commandline generate allure-results -o allure-report --clean
npx -y allure-commandline open allure-report
