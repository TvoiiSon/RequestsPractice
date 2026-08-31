import allure
import pytest
from requests import Response

from helpers.constants import WRONG_CREDENTIALS_DETAIL
from helpers.routes import Routes
from models.auth import Token
from models.common import ValidationErrorResponse
from models.user import UserResponse


@allure.epic("Auth")
@allure.feature("Registration")
class TestRegister:

    @allure.title("Регистрация с валидными данными")
    @allure.story("Успешная регистрация")
    @allure.description("POST /api/auth/register с валидным телом возвращает 200 и тело по схеме UserResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_register_valid(self, session, user_data: dict):
        resp: Response = session.post(Routes.REGISTER, json=user_data)
        assert resp.status_code == 200, resp.text

        body = resp.json()
        user = UserResponse.model_validate(body)
        assert user.email == user_data["email"]
        assert user.first_name == user_data["first_name"]
        assert user.last_name == user_data["last_name"]
        assert user.phone == user_data["phone"]
        assert "password" not in body

    @allure.title("Регистрация без поля phone → phone в ответе null")
    @allure.story("Успешная регистрация")
    @allure.description("POST /api/auth/register без необязательного phone возвращает 200; phone = null")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_register_without_phone(self, session, user_data: dict):
        del user_data["phone"]
        resp: Response = session.post(Routes.REGISTER, json=user_data)
        assert resp.status_code == 200, resp.text

        body = resp.json()
        user = UserResponse.model_validate(body)
        assert user.phone is None
        assert user.email == user_data["email"]
        assert "password" not in body

    @allure.title("Регистрация без обязательного поля {field} → 422")
    @allure.story("Валидация тела запроса")
    @allure.description("POST /api/auth/register без обязательного поля возвращает 422; поле есть в detail[*].loc")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize("field", ["email", "first_name", "last_name", "password"])
    def test_register_missing_required_field(self, session, user_data: dict, field):
        del user_data[field]
        resp = session.post(Routes.REGISTER, json=user_data)

        assert resp.status_code == 422, resp.text
        err = ValidationErrorResponse.model_validate(resp.json())
        assert any(field in item.loc for item in err.detail)

    @allure.title("Регистрация с невалидным полем {field}={value} → 422")
    @allure.story("Валидация тела запроса")
    @allure.description("POST /api/auth/register с невалидным значением поля возвращает 422; поле есть в detail[*].loc")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize("field, value, exp_type", [
        ("email", "not-an-email", "value_error"),
        ("password", "12345", "string_too_short"),
        ("first_name", 123, "string_type"),
    ], ids=["bad_email", "short_password", "wrong_type"])
    def test_register_invalid_field_value(self, session, user_data: dict, field, value, exp_type):
        user_data[field] = value
        resp = session.post(Routes.REGISTER, json=user_data)

        assert resp.status_code == 422, resp.text
        err = ValidationErrorResponse.model_validate(resp.json())
        assert any(field in item.loc for item in err.detail)
        assert any(i.type == exp_type and field in i.loc for i in err.detail)

    @allure.title("Повторная регистрация с тем же email → 400")
    @allure.story("Валидация тела запроса")
    @allure.description("Второй POST /api/auth/register с тем же email не создаёт пользователя (4xx, не 5xx)")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_register_duplicate_email(self, session, user_data: dict):
        first = session.post(Routes.REGISTER, json=user_data)
        assert first.status_code == 200, first.text

        second = session.post(Routes.REGISTER, json=user_data)
        assert 400 <= second.status_code < 500, second.text
        assert "detail" in second.json()

    @allure.title("Граничное значение поля {field} не роняет сервер")
    @allure.story("Граничные значения")
    @allure.description("Пустые/очень длинные строки и спецсимволы в полях не приводят к 5xx")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize("field, value", [
        ("email", ""),
        ("first_name", ""),
        ("first_name", "A" * 2000),
        ("first_name", "Иван 😀 <script> ' OR 1=1"),
    ], ids=["empty_email", "empty_first_name", "long_first_name", "special_chars"])
    def test_register_edge_values(self, session, user_data: dict, field, value):
        user_data[field] = value
        resp = session.post(Routes.REGISTER, json=user_data)
        assert resp.status_code < 500, resp.text


@allure.epic("Auth")
@allure.feature("Login")
class TestLogin:

    @allure.title("Логин с валидными данными → 200 + Token")
    @allure.story("Успешный вход")
    @allure.description("POST /api/auth/login с form-данными возвращает 200 и тело по схеме Token")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_login_valid(self, session, registered_user):
        creds = registered_user["request"]
        resp = session.post(
            Routes.LOGIN,
            data={"username": creds["email"], "password": creds["password"]},
        )

        assert resp.status_code == 200, resp.text
        token = Token.model_validate(resp.json())
        assert token.token_type == "bearer"
        assert token.access_token

    @allure.title("Логин с неверным паролем → 401")
    @allure.story("Ошибки входа")
    @allure.description("Верный email + неверный пароль: 401 и detail == 'Incorrect email or password'")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_login_wrong_password(self, session, registered_user):
        email = registered_user["request"]["email"]
        resp = session.post(Routes.LOGIN, data={"username": email, "password": "wrong-pass"})

        assert resp.status_code == 401, resp.text
        assert resp.json()["detail"] == WRONG_CREDENTIALS_DETAIL

    @allure.title("Логин несуществующим email → 401")
    @allure.story("Ошибки входа")
    @allure.description("Незарегистрированный email: 401 и detail == 'Incorrect email or password'")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_login_nonexistent_email(self, session, user_data):
        resp = session.post(
            Routes.LOGIN,
            data={"username": user_data["email"], "password": user_data["password"]},
        )

        assert resp.status_code == 401, resp.text
        assert resp.json()["detail"] == WRONG_CREDENTIALS_DETAIL

    @allure.title("Логин с некорректным email (без @) → 401")
    @allure.story("Ошибки входа")
    @allure.description("username 'example' вместо 'example@mail.com': 401 и detail с сообщением об ошибке")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_login_malformed_email(self, session):
        resp = session.post(Routes.LOGIN, data={"username": "example", "password": "whatever"})

        assert resp.status_code == 401, resp.text
        assert resp.json()["detail"] == WRONG_CREDENTIALS_DETAIL

    @allure.title("Логин без обязательного поля {field} → 422")
    @allure.story("Валидация тела запроса")
    @allure.description("POST /api/auth/login без обязательного поля формы возвращает 422; поле есть в detail[*].loc")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize("field", ["username", "password"])
    def test_login_missing_field(self, session, registered_user, field):
        creds = registered_user["request"]
        data = {"username": creds["email"], "password": creds["password"]}
        del data[field]
        resp = session.post(Routes.LOGIN, data=data)

        assert resp.status_code == 422, resp.text
        err = ValidationErrorResponse.model_validate(resp.json())
        assert any(field in item.loc for item in err.detail)

    @allure.title("Логин с телом JSON вместо формы → 422")
    @allure.story("Валидация тела запроса")
    @allure.description("POST /api/auth/login ожидает x-www-form-urlencoded; тело JSON возвращает 422")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_login_json_instead_of_form(self, session, registered_user):
        creds = registered_user["request"]
        resp = session.post(
            Routes.LOGIN,
            json={"username": creds["email"], "password": creds["password"]},
        )

        assert resp.status_code == 422, resp.text
