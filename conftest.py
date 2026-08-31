import base64
import logging
import allure
import pytest
import requests
from config import BASE_URL
from loguru import logger
from helpers.data_generator import generate_user, generate_article

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
def png_image() -> tuple:
    """1x1 PNG, готовый для files={"image": png_image}."""
    data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
        "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    )
    return ("test.png", data, "image/png")

# ---------- пользователи / авторизация ----------

@pytest.fixture
def registered_user(session) -> dict:
    user = generate_user()
    resp = session.post("/api/auth/register", json=user)
    assert resp.status_code == 200, resp.text
    return {"request": user, "response": resp.json()}

@pytest.fixture
def auth_session(registered_user):
    """Отдельный клиент с заголовком Authorization - не трогает анонимный session."""
    creds = registered_user["request"]
    client = ApiClient()
    resp = client.post("/api/auth/login", data={"username": creds["email"], "password": creds["password"]})
    assert resp.status_code == 200, resp.text
    client.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
    yield client
    client.close()

# ---------- новости ----------

@pytest.fixture
def created_news(auth_session, article_data) -> dict:
    resp = auth_session.post("/api/news/", data=article_data)
    assert resp.status_code == 200, resp.text
    return resp.json()
