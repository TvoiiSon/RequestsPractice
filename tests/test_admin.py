"""Тесты админ-раздела /api/admin/* на заглушках.

Эндпоинты /api/admin/* есть в API, но вне списка задания, требуют прав
администратора, а их тело ответа в Swagger не описано ({}). Здесь
проверяется работа с ними на мок-ответах: коды ответа и предполагаемая
форма тела - без обращения к реальному серверу.
"""
import allure
import pytest

from helpers.constants import MISSING_ID
from helpers.routes import Routes
from models.common import Page
from models.user import UserResponse


@allure.epic("Admin")
@allure.feature("Admin (mocked)")
@pytest.mark.mock
@pytest.mark.api
class TestAdminMocked:

    @allure.title("GET /api/admin/users → 200, страница пользователей (мок)")
    @allure.story("Управление пользователями")
    @allure.description("Мок страницы Page[UserResponse]; проверяем контракт и total")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_list_users(self, session, mock_api, mock_user):
        mock_api(200, {"items": [mock_user], "total": 1, "page": 1, "per_page": 20, "total_pages": 1})

        resp = session.get(Routes.ADMIN_USERS)

        assert resp.status_code == 200
        page = Page[UserResponse].model_validate(resp.json())
        assert page.total == 1
        assert page.items[0].email == mock_user["email"]

    @allure.title("GET /api/admin/stats → 200, счётчики (мок)")
    @allure.story("Статистика")
    @allure.description("Мок объекта со счётчиками; все значения - целые числа")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_stats(self, session, mock_api):
        mock_api(200, {"users": 10, "news": 5, "comments": 42})

        resp = session.get(Routes.ADMIN_STATS)

        assert resp.status_code == 200
        body = resp.json()
        assert set(body) == {"users", "news", "comments"}
        assert all(isinstance(v, int) for v in body.values())

    @allure.title("PUT /api/admin/users/{id}/toggle-active → 200 (мок)")
    @allure.story("Управление пользователями")
    @allure.description("Мок 200 с телом пользователя; ответ соответствует схеме UserResponse")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_toggle_active(self, session, mock_api, mock_user):
        mock_api(200, mock_user)

        resp = session.put(Routes.admin_user_toggle(mock_user["id"]))

        assert resp.status_code == 200
        UserResponse.model_validate(resp.json())

    @allure.title("DELETE /api/admin/users/{id} → 200 (мок)")
    @allure.story("Управление пользователями")
    @allure.description("Мок 200 с detail об удалении")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_delete_user(self, session, mock_api, mock_user):
        mock_api(200, {"detail": "User deleted"})

        resp = session.delete(Routes.admin_user(mock_user["id"]))

        assert resp.status_code == 200
        assert "detail" in resp.json()

    @allure.title("GET /api/admin/users обычным пользователем → 403 (мок)")
    @allure.story("Права доступа")
    @allure.description("Мок 403 с detail; проверяем код и наличие сообщения")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.negative
    def test_forbidden_for_non_admin(self, session, mock_api):
        mock_api(403, {"detail": "Forbidden"})

        resp = session.get(Routes.ADMIN_USERS)

        assert resp.status_code == 403
        assert resp.json()["detail"]

    @allure.title("DELETE /api/admin/users/{id} с несуществующим id → 404 (мок)")
    @allure.story("Управление пользователями")
    @allure.description("Мок 404 при удалении несуществующего пользователя")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.negative
    def test_delete_user_not_found(self, session, mock_api):
        mock_api(404, {"detail": "User not found"})

        resp = session.delete(Routes.admin_user(MISSING_ID))

        assert resp.status_code == 404
        assert resp.json()["detail"]
