"""Тесты профиля /api/users/me на заглушках.

Эндпоинты /api/users/me есть в API, но вне списка задания и требуют
токена. Здесь проверяется работа с ними на мок-ответах: контракт
(Pydantic-модель) и коды ответа - без обращения к реальному серверу.
"""
import allure
import pytest

from helpers.routes import Routes
from models.user import UserResponse


@allure.epic("Users")
@allure.feature("Profile (mocked)")
@pytest.mark.mock
@pytest.mark.api
class TestUsersMeMocked:

    @allure.title("GET /api/users/me → 200 + UserResponse (мок)")
    @allure.story("Профиль")
    @allure.description("Мок 200 с телом профиля; проверяем контракт UserResponse и поля")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_get_me(self, session, mock_api, mock_user):
        mock_api(200, mock_user)

        resp = session.get(Routes.USERS_ME)

        assert resp.status_code == 200
        user = UserResponse.model_validate(resp.json())
        assert user.id == mock_user["id"]
        assert user.email == mock_user["email"]

    @allure.title("PUT /api/users/me меняет first_name → 200 (мок)")
    @allure.story("Профиль")
    @allure.description("Мок 200 с обновлённым телом; в ответе новое first_name")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_update_me(self, session, mock_api, mock_user):
        new_name = mock_user["first_name"] + "-updated"
        mock_api(200, {**mock_user, "first_name": new_name})

        resp = session.put(Routes.USERS_ME, json={"first_name": new_name})

        assert resp.status_code == 200
        user = UserResponse.model_validate(resp.json())
        assert user.first_name == new_name

    @allure.title("POST /api/users/me/photo → 200, photo_path заполнен (мок)")
    @allure.story("Профиль")
    @allure.description("Мок 200 с непустым photo_path после загрузки файла")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_upload_photo(self, session, mock_api, mock_user, png_image):
        mock_api(200, {**mock_user, "photo_path": f"/uploads/user_{mock_user['id']}.png"})

        resp = session.post(Routes.USERS_ME_PHOTO, files={"photo": png_image})

        assert resp.status_code == 200
        user = UserResponse.model_validate(resp.json())
        assert user.photo_path is not None

    @allure.title("GET /api/users/me без токена → 401 (мок)")
    @allure.story("Профиль")
    @allure.description("Мок 401 с detail; проверяем код и наличие сообщения")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.negative
    def test_get_me_unauthorized(self, session, mock_api):
        mock_api(401, {"detail": "Not authenticated"})

        resp = session.get(Routes.USERS_ME)

        assert resp.status_code == 401
        assert resp.json()["detail"]
