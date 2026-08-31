"""Тесты профиля /api/users/me на заглушках.

Эндпоинты /api/users/me есть в API, но вне списка задания и требуют
токена. Здесь проверяется работа с ними на мок-ответах: контракт
(Pydantic-модель) и коды ответа - без обращения к реальному серверу.
"""
import allure
import pytest

from models.user import UserResponse

VALID_USER = {
    "id": 1,
    "email": "user@example.com",
    "first_name": "Иван",
    "last_name": "Петров",
    "phone": None,
    "photo_path": None,
    "created_at": "2026-01-01T12:00:00",
}


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
    def test_get_me(self, session, mock_api):
        mock_api(200, VALID_USER)

        resp = session.get("/api/users/me")

        assert resp.status_code == 200
        user = UserResponse.model_validate(resp.json())
        assert user.id == VALID_USER["id"]
        assert user.email == VALID_USER["email"]

    @allure.title("PUT /api/users/me меняет first_name → 200 (мок)")
    @allure.story("Профиль")
    @allure.description("Мок 200 с обновлённым телом; в ответе новое first_name")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_update_me(self, session, mock_api):
        mock_api(200, {**VALID_USER, "first_name": "Пётр"})

        resp = session.put("/api/users/me", json={"first_name": "Пётр"})

        assert resp.status_code == 200
        user = UserResponse.model_validate(resp.json())
        assert user.first_name == "Пётр"

    @allure.title("POST /api/users/me/photo → 200, photo_path заполнен (мок)")
    @allure.story("Профиль")
    @allure.description("Мок 200 с непустым photo_path после загрузки файла")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.positive
    def test_upload_photo(self, session, mock_api):
        mock_api(200, {**VALID_USER, "photo_path": "/uploads/user_1.png"})

        resp = session.post("/api/users/me/photo", files={"photo": ("a.png", b"x", "image/png")})

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

        resp = session.get("/api/users/me")

        assert resp.status_code == 401
        assert resp.json()["detail"]
