# UI autotests (Python + Selenium + Pytest + Allure)

## 1) Создайте окружение и активируйте его
python -m venv venv
.\venv\Scripts\Activate


## 2) Установите зависимости
```powershell
pip install -r requirements.txt
```

## 3) Запустите тесты
По отдельности:
pytest tests\test_case_01_multiplayer_flow.py 
Или все
pytest tests

Чтобы окно браузера было видно:
$env:HEADLESS="false"

Консольный режим:
$env:HEADLESS="true"


## 4) Allure отчет 
Отчет автоматический генирируется, но если нужно чтобы генерировался в другую папку можно запустить тесты с параметром alluredir
pytest tests --alluredir=allure-results
```

Открыть отчет Allure
npx -y allure-commandline serve allure-results

