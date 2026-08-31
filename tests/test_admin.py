import pytest
import allure
from loguru import logger

from helpers.constants import MISSING_ID
from helpers.routes import Routes
from models.common import Page
from models.user import UserResponse


class TestAdmin:
    @allure.epic("NewsPlatform")
    @allure.feature("Админка (моки)")
    @allure.story("Список пользователей")
    @allure.description("GET /api/admin/users на мок-ответе 200 возвращает страницу Page[UserResponse]")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.positive
    def test_list_users(self, session, mock_api, mock_user):
        with allure.step("Мок страницы пользователей, проверка контракта Page[UserResponse]"):
            logger.info("Мок страницы пользователей, проверка контракта Page[UserResponse]")
            mock_api(200, {"items": [mock_user], "total": 1, "page": 1, "per_page": 20, "total_pages": 1})
            response = session.get(Routes.ADMIN_USERS)

            assert response.status_code == 200, response.text
            page = Page[UserResponse].model_validate(response.json())
            assert page.total == 1, "total в ответе не совпал с ожидаемым"
            assert page.items[0].email == mock_user["email"], "email первого пользователя не совпал"

    @allure.epic("NewsPlatform")
    @allure.feature("Админка (моки)")
    @allure.story("Статистика")
    @allure.description("GET /api/admin/stats на мок-ответе 200 возвращает объект со счётчиками-числами")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.positive
    def test_stats(self, session, mock_api):
        with allure.step("Мок объекта со счётчиками, проверка ключей и типов значений"):
            logger.info("Мок объекта со счётчиками, проверка ключей и типов значений")
            mock_api(200, {"users": 10, "news": 5, "comments": 42})
            response = session.get(Routes.ADMIN_STATS)

            assert response.status_code == 200, response.text
            body = response.json()
            assert set(body) == {"users", "news", "comments"}, "Набор ключей статистики не совпал с ожидаемым"
            assert all(isinstance(value, int) for value in body.values()), "Значения статистики должны быть числами"

    @allure.epic("NewsPlatform")
    @allure.feature("Админка (моки)")
    @allure.story("Переключение активности пользователя")
    @allure.description("PUT /api/admin/users/{id}/toggle-active на мок-ответе 200 возвращает тело по схеме UserResponse")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.positive
    def test_toggle_active(self, session, mock_api, mock_user):
        with allure.step("Мок 200 с телом пользователя, проверка контракта UserResponse"):
            logger.info("Мок 200 с телом пользователя, проверка контракта UserResponse")
            mock_api(200, mock_user)
            response = session.put(Routes.admin_user_toggle(mock_user["id"]))

            assert response.status_code == 200, response.text
            UserResponse.model_validate(response.json())

    @allure.epic("NewsPlatform")
    @allure.feature("Админка (моки)")
    @allure.story("Удаление пользователя")
    @allure.description("DELETE /api/admin/users/{id} на мок-ответе 200 возвращает detail об удалении")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.positive
    def test_delete_user(self, session, mock_api, mock_user):
        with allure.step("Мок 200 с detail об удалении"):
            logger.info("Мок 200 с detail об удалении")
            mock_api(200, {"detail": "User deleted"})
            response = session.delete(Routes.admin_user(mock_user["id"]))

            assert response.status_code == 200, response.text
            assert "detail" in response.json(), "В ответе нет detail об удалении"

    @allure.epic("NewsPlatform")
    @allure.feature("Админка (моки)")
    @allure.story("Доступ обычного пользователя к админке")
    @allure.description("GET /api/admin/users на мок-ответе 403 возвращает detail с сообщением")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.negative
    def test_forbidden_for_non_admin(self, session, mock_api):
        with allure.step("Мок 403 с detail, проверка кода и наличия сообщения"):
            logger.info("Мок 403 с detail, проверка кода и наличия сообщения")
            mock_api(403, {"detail": "Forbidden"})
            response = session.get(Routes.ADMIN_USERS)

            assert response.status_code == 403, response.text
            assert response.json()["detail"], "В ответе нет detail с описанием ошибки"

    @allure.epic("NewsPlatform")
    @allure.feature("Админка (моки)")
    @allure.story("Удаление несуществующего пользователя")
    @allure.description("DELETE /api/admin/users/{id} на мок-ответе 404 возвращает detail")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.negative
    def test_delete_user_not_found(self, session, mock_api):
        with allure.step("Мок 404 при удалении несуществующего пользователя"):
            logger.info("Мок 404 при удалении несуществующего пользователя")
            mock_api(404, {"detail": "User not found"})
            response = session.delete(Routes.admin_user(MISSING_ID))

            assert response.status_code == 404, response.text
            assert response.json()["detail"], "В ответе нет detail с описанием ошибки"
