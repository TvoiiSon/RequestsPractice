import pytest
import allure
from loguru import logger

from helpers.routes import Routes
from models.user import UserResponse


class TestUsersMe:
    @allure.epic("NewsPlatform")
    @allure.feature("Профиль (моки)")
    @allure.story("Получение своего профиля")
    @allure.description("GET /api/users/me на мок-ответе 200 возвращает тело по схеме UserResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.positive
    def test_get_me(self, session, mock_api, mock_user):
        with allure.step("Мок 200 с телом профиля, проверка контракта UserResponse"):
            logger.info("Мок 200 с телом профиля, проверка контракта UserResponse")
            mock_api(200, mock_user)
            response = session.get(Routes.USERS_ME)

            assert response.status_code == 200, response.text
            user = UserResponse.model_validate(response.json())
            assert user.id == mock_user["id"], "id в ответе не совпал с ожидаемым"
            assert user.email == mock_user["email"], "email в ответе не совпал с ожидаемым"

    @allure.epic("NewsPlatform")
    @allure.feature("Профиль (моки)")
    @allure.story("Редактирование своего профиля")
    @allure.description("PUT /api/users/me на мок-ответе 200 возвращает обновлённое first_name")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.positive
    def test_update_me(self, session, mock_api, mock_user):
        with allure.step("Мок 200 с обновлённым телом, проверка нового first_name"):
            logger.info("Мок 200 с обновлённым телом, проверка нового first_name")
            new_name = mock_user["first_name"] + "-updated"
            mock_api(200, {**mock_user, "first_name": new_name})
            response = session.put(Routes.USERS_ME, json={"first_name": new_name})

            assert response.status_code == 200, response.text
            user = UserResponse.model_validate(response.json())
            assert user.first_name == new_name, "first_name в ответе не обновился"

    @allure.epic("NewsPlatform")
    @allure.feature("Профиль (моки)")
    @allure.story("Загрузка фото профиля")
    @allure.description("POST /api/users/me/photo на мок-ответе 200 возвращает непустой photo_path")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.positive
    def test_upload_photo(self, session, mock_api, mock_user, image_file):
        with allure.step("Мок 200 с непустым photo_path после загрузки файла"):
            logger.info("Мок 200 с непустым photo_path после загрузки файла")
            mock_api(200, {**mock_user, "photo_path": f"/uploads/user_{mock_user['id']}.png"})
            response = session.post(Routes.USERS_ME_PHOTO, files={"photo": image_file})

            assert response.status_code == 200, response.text
            user = UserResponse.model_validate(response.json())
            assert user.photo_path is not None, "photo_path должен быть заполнен после загрузки"

    @allure.epic("NewsPlatform")
    @allure.feature("Профиль (моки)")
    @allure.story("Профиль без токена")
    @allure.description("GET /api/users/me на мок-ответе 401 возвращает detail с сообщением")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.mock
    @pytest.mark.negative
    def test_get_me_unauthorized(self, session, mock_api):
        with allure.step("Мок 401 с detail, проверка кода и наличия сообщения"):
            logger.info("Мок 401 с detail, проверка кода и наличия сообщения")
            mock_api(401, {"detail": "Not authenticated"})
            response = session.get(Routes.USERS_ME)

            assert response.status_code == 401, response.text
            assert response.json()["detail"], "В ответе нет detail с описанием ошибки"
