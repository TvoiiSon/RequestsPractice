import pytest
import allure
import requests
import logging
from config import BASE_URL
from loguru import logger
from helpers.data_generator import generate_user

class PropagateHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)

@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    logger.remove()
    logger.add(PropagateHandler(), format="{message}", level="DEBUG")
    yield

class ApiClient(requests.Session):
    def __init__(self):
        super().__init__()
        self.last_response: requests.Response | None = None

    def request(self, method, url, *args, **kwargs) -> requests.Response:
        resp = super().request(method, BASE_URL + url, *args, **kwargs)
        self.last_response = resp
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
def attach_on_failure(request, session):
    yield
    rep = getattr(request.node, "rep_call", None)
    if rep and rep.failed and session.last_response is not None:
        r = session.last_response
        allure.attach(
            f"{r.request.method} {r.request.url}\n"
            f"request body: {r.request.body}\n\n"
            f"status: {r.status_code}\n"
            f"response: {r.text}",
            name="last HTTP exchange",
            attachment_type=allure.attachment_type.TEXT,
        )

@pytest.fixture(scope="function")
def user_data():
    return generate_user()
