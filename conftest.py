import logging
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import allure
import requests
from loguru import logger

from config import ADMIN_TOKEN, BASE_URL
from helpers.constants import INVALID_TOKEN
from helpers.data_generator import generate_article, generate_comment, generate_user, generate_user_response
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
        response = super().request(method, BASE_URL + url, *args, **kwargs)
        self.last_response = response
        ApiClient.last_any = response
        return response


def admin_cleanup(path):
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
    response = ApiClient.last_any
    if rep and rep.failed and response is not None:
        allure.attach(
            f"{response.request.method} {response.request.url}\n"
            f"request body: {response.request.body}\n\n"
            f"status: {response.status_code}\n"
            f"response: {response.text}",
            name="last HTTP exchange",
            attachment_type=allure.attachment_type.TEXT,
        )


@pytest.fixture
def user_data():
    return generate_user()


@pytest.fixture
def article_data():
    return generate_article()


@pytest.fixture
def mock_user():
    return generate_user_response()


@pytest.fixture
def image_file():
    path = TEST_DATA / "images.jpeg"
    return (path.name, path.read_bytes(), "image/jpeg")


@pytest.fixture
def registered_user(session):
    user = generate_user()
    response = session.post(Routes.REGISTER, json=user)
    assert response.status_code == 200, response.text
    body = response.json()
    logger.info(f"Регистрация пользователя email: {user['email']}")
    yield {"request": user, "response": body}
    admin_cleanup(Routes.admin_user(body["id"]))


@pytest.fixture
def auth_session(registered_user):
    creds = registered_user["request"]
    client = ApiClient()
    response = client.post(Routes.LOGIN, data={"username": creds["email"], "password": creds["password"]})
    assert response.status_code == 200, response.text
    client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"
    logger.info(f"Авторизация под пользователем email: {creds['email']}")
    yield client
    client.close()


@pytest.fixture
def bad_token_session():
    client = ApiClient()
    client.headers["Authorization"] = INVALID_TOKEN
    yield client
    client.close()


@pytest.fixture
def mock_api(monkeypatch):
    queue = []

    def fake_request(self, method, url, *args, **kwargs):
        assert queue, f"Неожиданный запрос {method} {url}: мок-ответы кончились"
        response = queue.pop(0)
        response.request = MagicMock(method=method, url=url, body=kwargs.get("json") or kwargs.get("data"))
        ApiClient.last_any = response
        return response

    monkeypatch.setattr(ApiClient, "request", fake_request)

    def add(status=200, json_body=None, text=None):
        response = MagicMock(spec=requests.Response)
        response.status_code = status
        response.ok = status < 400
        response.json.return_value = {} if json_body is None else json_body
        response.text = text if text is not None else str(json_body)
        queue.append(response)
        return response

    return add


@pytest.fixture
def created_news(auth_session, article_data):
    response = auth_session.post(Routes.NEWS, data=article_data)
    assert response.status_code == 200, response.text
    news = response.json()
    logger.info(f"Создана новость id={news['id']} title={news['title']}")
    yield news
    admin_cleanup(Routes.admin_news(news["id"]))


@pytest.fixture
def add_comment(auth_session):
    def _add(news_id, text=None):
        text = text or generate_comment()
        response = auth_session.post(Routes.news_comments(news_id), json={"text": text})
        return text, response

    return _add
