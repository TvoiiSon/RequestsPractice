import allure
import pytest
from requests import Response
from models.common import ValidationErrorResponse
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
        assert resp.status_code == 200, resp.text

        body = resp.json()
        user = UserResponse.model_validate(body)
        assert user.email == user_data["email"]
        assert "password" not in body

    @allure.title("Регистрация без поля phone → phone в ответе null")
    @allure.story("Успешная регистрация")
    @allure.description("POST /api/auth/register без необязательного phone возвращает 200; в ответе phone = null")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_register_without_phone(self, session, user_data: dict):
        del user_data["phone"]
        resp: Response = session.post("/api/auth/register", json=user_data)
        assert resp.status_code == 200, resp.text
        
        body = resp.json()
        user = UserResponse.model_validate(body)
        assert user.phone is None
        assert user.email == user_data["email"]
        assert "password" not in body

    @allure.title("Регистрация без обязательного поля {field} → 422")
    @allure.story("Валидация тела запроса")
    @allure.description(
        "POST /api/auth/register без обязательного поля возвращает 422, "
        "поле присутствует в detail[*].loc ответа"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.parametrize("field", ["email", "first_name", "last_name", "password"])
    def test_register_missing_required_field(self, session, user_data: dict, field):
        del user_data[field]
        resp = session.post("/api/auth/register", json=user_data)

        assert resp.status_code == 422, resp.text
        err = ValidationErrorResponse.model_validate(resp.json())
        assert any(field in item.loc for item in err.detail)

    @allure.title("Регистрация с невалидным полем {field}={value} → 422")
    @allure.story("Валидация тела запроса")
    @allure.description(
        "POST /api/auth/register с невалидным значением поля возвращает 422, "
        "поле присутствует в detail[*].loc ответа"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.parametrize("field, value, exp_type", [
        ("email", "not-an-email", "value_error"),
        ("password", "12345", "string_too_short"),
        ("first_name", 123, "string_type"),
    ], ids=["bad_email", "short_password", "wrong_type"])
    def test_register_invalid_field_value(self, session, user_data: dict, field, value, exp_type):
        user_data[field] = value
        resp = session.post("/api/auth/register", json=user_data)

        assert resp.status_code == 422, resp.text
        err = ValidationErrorResponse.model_validate(resp.json())
        assert any(field in item.loc for item in err.detail)
    