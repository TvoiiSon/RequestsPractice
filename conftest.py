import base64
import logging
from pathlib import Path
from unittest.mock import MagicMock

import allure
import pytest
import requests
from loguru import logger

from config import ADMIN_TOKEN, BASE_URL
from helpers.constants import INVALID_TOKEN
from helpers.data_generator import (
    generate_article,
    generate_comment,
    generate_user,
    generate_user_response,
)
from helpers.routes import Routes

TEST_DATA = Path(__file__).parent / "test_data"


class PropagateHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    logger.remove()
    logger.add(PropagateHandler(), format="{message}", level="DEBUG")
    yield


class ApiClient(requests.Session):
    last_any: requests.Response | None = None

    def __init__(self):
        super().__init__()
        self.last_response: requests.Response | None = None

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        resp = super().request(method, BASE_URL + url, *args, **kwargs)
        self.last_response = resp
        ApiClient.last_any = resp
        return resp


def _admin_cleanup(path: str) -> None:
    """Best-effort удаление созданной сущности. Требует ADMIN_TOKEN, иначе no-op
    (у API нет публичных DELETE-эндпоинтов)."""
    if not ADMIN_TOKEN:
        return
    client = ApiClient()
    client.headers["Authorization"] = f"Bearer {ADMIN_TOKEN}"
    try:
        client.delete(path)
    except requests.RequestException:
        pass
    finally:
        client.close()


@pytest.fixture(scope="session")
def session():
    client = ApiClient()
    yield client
    client.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def attach_on_failure(request):
    yield
    rep = getattr(request.node, "rep_call", None)
    r = ApiClient.last_any
    if rep and rep.failed and r is not None:
        allure.attach(
            f"{r.request.method} {r.request.url}\n"
            f"request body: {r.request.body}\n\n"
            f"status: {r.status_code}\n"
            f"response: {r.text}",
            name="last HTTP exchange",
            attachment_type=allure.attachment_type.TEXT,
        )


# ---------- данные ----------

@pytest.fixture
def user_data() -> dict:
    return generate_user()


@pytest.fixture
def article_data() -> dict:
    return generate_article()


@pytest.fixture
def mock_user() -> dict:
    """Тело по схеме UserResponse для мок-ответов."""
    return generate_user_response()


@pytest.fixture
def png_image() -> tuple:
    """1x1 PNG в памяти - для мок-загрузки файла (без обращения к диску)."""
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    return ("test.png", data, "image/png")


@pytest.fixture
def news_image() -> tuple:
    """Реальный файл из test_data/ для загрузки изображения новости."""
    path = TEST_DATA / "images.jpeg"
    return (path.name, path.read_bytes(), "image/jpeg")


# ---------- пользователи / авторизация ----------

@pytest.fixture
def registered_user(session) -> dict:
    user = generate_user()
    resp = session.post(Routes.REGISTER, json=user)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    yield {"request": user, "response": body}
    _admin_cleanup(Routes.admin_user(body["id"]))


@pytest.fixture
def auth_session(registered_user):
    """Отдельный клиент с заголовком Authorization - не трогает анонимный session."""
    creds = registered_user["request"]
    client = ApiClient()
    resp = client.post(Routes.LOGIN, data={"username": creds["email"], "password": creds["password"]})
    assert resp.status_code == 200, resp.text
    client.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
    yield client
    client.close()


@pytest.fixture
def bad_token_session():
    """Клиент с заведомо невалидным токеном - для проверки отказа в доступе."""
    client = ApiClient()
    client.headers["Authorization"] = INVALID_TOKEN
    yield client
    client.close()


# ---------- заглушки (моки) ----------

@pytest.fixture
def mock_api(monkeypatch):
    """Подменяет ApiClient.request очередью заранее заданных ответов - реальный API не вызывается.

    mock_api(200, {"id": 1, ...})          # один ответ
    mock_api(200, {...}); mock_api(404)    # несколько ответов подряд
    """
    queue: list[MagicMock] = []

    def fake_request(self, method, url, *args, **kwargs):
        assert queue, f"неожиданный запрос {method} {url}: мок-ответы кончились"
        resp = queue.pop(0)
        resp.request = MagicMock(method=method, url=url,
                                 body=kwargs.get("json") or kwargs.get("data"))
        ApiClient.last_any = resp
        return resp

    monkeypatch.setattr(ApiClient, "request", fake_request)

    def add(status: int = 200, json_body=None, text: str | None = None) -> MagicMock:
        resp = MagicMock(spec=requests.Response)
        resp.status_code = status
        resp.ok = status < 400
        resp.json.return_value = {} if json_body is None else json_body
        resp.text = text if text is not None else str(json_body)
        queue.append(resp)
        return resp

    return add


# ---------- новости / комментарии ----------

@pytest.fixture
def created_news(auth_session, article_data) -> dict:
    resp = auth_session.post(Routes.NEWS, data=article_data)
    assert resp.status_code == 200, resp.text
    news = resp.json()
    yield news
    _admin_cleanup(Routes.admin_news(news["id"]))


@pytest.fixture
def add_comment(auth_session):
    """Добавляет комментарий к новости, возвращает (text, response)."""
    def _add(news_id, text: str | None = None):
        text = text or generate_comment()
        resp = auth_session.post(Routes.news_comments(news_id), json={"text": text})
        return text, resp
    return _add
