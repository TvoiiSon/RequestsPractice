import allure
import pytest
from requests import Response
from models.user import UserResponse

@allure.epic("Auth")
@allure.feature("Registration")
class TestRegister:
    @allure.title("Регистрация с валидными данными")
    @allure.story("Успешная регистрация")
    @allure.description("POST /api/auth/register с валидным телом возвращает 200 и тело, соответствующее схеме UserResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_register_valid(self, session, user_data: dict):
        resp: Response = session.post("/api/auth/register", json=user_data)
        user = UserResponse.model_validate(resp.json())

        assert resp.status_code == 200, resp.text
        assert user.email == user_data["email"]
        assert "password" not in resp.json()
        