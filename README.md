# RequestsPractice

API-автотесты для https://archiscope.ru (`requests` + `pydantic` + `pytest` + `allure`).

## Запуск

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pytest
```

Отчёт Allure:

```bash
pytest --alluredir=allure-results
allure serve allure-results
```

## Конфигурация (переменные окружения)

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `BASE_URL` | `https://archiscope.ru` | базовый адрес API |
| `ADMIN_TOKEN` | `` (пусто) | токен админа для очистки тестовых данных после прогона |

## Маркеры

`api`, `smoke`, `regression`, `positive`, `negative`, `mock`.

```bash
pytest -m smoke
pytest -m "negative and not mock"
```

## Структура

```
config.py              BASE_URL / ADMIN_TOKEN из окружения
conftest.py            ApiClient, фикстуры (session, auth_session, registered_user,
                       created_news, add_comment, mock_api, ...), хук attach_on_failure
helpers/
  routes.py            пути эндпоинтов (без хардкода строк в тестах)
  constants.py         общие значения (MISSING_ID, NON_NUMERIC_ID, ...)
  data_generator.py    Faker-генераторы тел запросов и мок-ответов
models/                Pydantic-модели запросов/ответов по OpenAPI-схемам
tests/
  test_auth.py         регистрация, логин
  test_news.py         CRUD новостей, теги
  test_comments.py     комментарии
  test_users.py        /api/users/me - на заглушках (@mock)
  test_admin.py        /api/admin/* - на заглушках (@mock)
```

## Очистка тестовых данных

У API нет публичных `DELETE`-эндпоинтов (только `/api/admin/*` под правами
администратора). Фикстуры `registered_user` и `created_news` вызывают
best-effort удаление через админ-эндпоинты, **только если задан `ADMIN_TOKEN`**;
без него созданные в ходе тестов сущности остаются на сервере.

## Мок-тесты

`test_users.py` и `test_admin.py` покрывают эндпоинты вне списка задания
(требуют токена / прав админа). Фикстура `mock_api` подменяет `ApiClient.request`
очередью заготовленных ответов — реальный сервер не вызывается.
