import pytest
import allure
from loguru import logger

from helpers.constants import WRONG_CREDENTIALS_DETAIL
from helpers.routes import Routes
from models.auth import Token
from models.common import ValidationErrorResponse
from models.user import UserResponse


class TestRegister:
    @allure.epic("NewsPlatform")
    @allure.feature("Регистрация")
    @allure.story("Успешная регистрация")
    @allure.description("POST /api/auth/register с валидным телом возвращает 200 и тело по схеме UserResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.positive
    def test_register_valid(self, session, user_data):
        with allure.step("Регистрация с валидными данными, проверка тела ответа по схеме UserResponse"):
            logger.info("Регистрация с валидными данными, проверка тела ответа по схеме UserResponse")
            response = session.post(Routes.REGISTER, json=user_data)

            assert response.status_code == 200, response.text
            body = response.json()
            user = UserResponse.model_validate(body)
            assert user.email == user_data["email"], "email в ответе не совпал с отправленным"
            assert user.first_name == user_data["first_name"], "first_name в ответе не совпал с отправленным"
            assert user.last_name == user_data["last_name"], "last_name в ответе не совпал с отправленным"
            assert user.phone == user_data["phone"], "phone в ответе не совпал с отправленным"
            assert "password" not in body, "Пароль не должен возвращаться в ответе"

    @allure.epic("NewsPlatform")
    @allure.feature("Регистрация")
    @allure.story("Регистрация без необязательного телефона")
    @allure.description("POST /api/auth/register без поля phone возвращает 200, phone в ответе null")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.positive
    def test_register_without_phone(self, session, user_data):
        with allure.step("Регистрация без поля phone, проверка что phone в ответе null"):
            logger.info("Регистрация без поля phone, проверка что phone в ответе null")
            del user_data["phone"]
            response = session.post(Routes.REGISTER, json=user_data)

            assert response.status_code == 200, response.text
            body = response.json()
            user = UserResponse.model_validate(body)
            assert user.phone is None, "phone должен быть null, если не передан"
            assert user.email == user_data["email"], "email в ответе не совпал с отправленным"
            assert "password" not in body, "Пароль не должен возвращаться в ответе"

    @allure.epic("NewsPlatform")
    @allure.feature("Регистрация")
    @allure.story("Пустое обязательное поле регистрации")
    @allure.description("POST /api/auth/register без обязательного поля возвращает 422, поле присутствует в detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.parametrize("field", ["email", "first_name", "last_name", "password"])
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_register_missing_required_field(self, session, user_data, field):
        with allure.step(f"Регистрация без обязательного поля {field}, ожидаем 422"):
            logger.info(f"Регистрация без обязательного поля {field}, ожидаем 422")
            del user_data[field]
            response = session.post(Routes.REGISTER, json=user_data)

            assert response.status_code == 422, response.text
            err = ValidationErrorResponse.model_validate(response.json())
            assert any(field in item.loc for item in err.detail), f"Поля {field} нет в detail ответа"

    @allure.epic("NewsPlatform")
    @allure.feature("Регистрация")
    @allure.story("Невалидное значение поля регистрации")
    @allure.description("POST /api/auth/register с невалидным значением поля возвращает 422 с ожидаемым type ошибки")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.parametrize("field, value, exp_type", [
        ("email", "not-an-email", "value_error"),
        ("password", "12345", "string_too_short"),
        ("first_name", 123, "string_type"),
    ], ids=["bad_email", "short_password", "wrong_type"])
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_register_invalid_field_value(self, session, user_data, field, value, exp_type):
        with allure.step(f"Регистрация с невалидным {field}={value}, ожидаем 422 и type {exp_type}"):
            logger.info(f"Регистрация с невалидным {field}={value}, ожидаем 422 и type {exp_type}")
            user_data[field] = value
            response = session.post(Routes.REGISTER, json=user_data)

            assert response.status_code == 422, response.text
            err = ValidationErrorResponse.model_validate(response.json())
            assert any(field in item.loc for item in err.detail), f"Поля {field} нет в detail ответа"
            assert any(i.type == exp_type and field in i.loc for i in err.detail), f"Ожидали type {exp_type} для поля {field}"

    @allure.epic("NewsPlatform")
    @allure.feature("Регистрация")
    @allure.story("Регистрация на уже занятый email")
    @allure.description("Повторный POST /api/auth/register с тем же email отклоняется клиентской ошибкой, не 5xx")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_register_duplicate_email(self, session, user_data):
        with allure.step("Регистрация того же email дважды, второй раз ожидаем 4xx"):
            logger.info("Регистрация того же email дважды, второй раз ожидаем 4xx")
            first = session.post(Routes.REGISTER, json=user_data)
            assert first.status_code == 200, first.text

            second = session.post(Routes.REGISTER, json=user_data)
            assert 400 <= second.status_code < 500, f"Ожидали 4xx на дубль email, получили {second.status_code}"
            assert "detail" in second.json(), "В ответе нет detail с описанием ошибки"

    @allure.epic("NewsPlatform")
    @allure.feature("Регистрация")
    @allure.story("Граничные значения полей регистрации")
    @allure.description("Пустые, очень длинные строки и спецсимволы в полях не приводят к 5xx")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.parametrize("field, value", [
        ("email", ""),
        ("first_name", ""),
        ("first_name", "A" * 2000),
        ("first_name", "Иван 😀 <script> ' OR 1=1"),
    ], ids=["empty_email", "empty_first_name", "long_first_name", "special_chars"])
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_register_edge_values(self, session, user_data, field, value):
        with allure.step(f"Регистрация с граничным значением поля {field}, сервер не должен падать"):
            logger.info(f"Регистрация с граничным значением поля {field}, сервер не должен падать")
            user_data[field] = value
            response = session.post(Routes.REGISTER, json=user_data)

            assert response.status_code < 500, f"Сервер упал с {response.status_code} на граничном значении"


class TestLogin:
    @allure.epic("NewsPlatform")
    @allure.feature("Авторизация")
    @allure.story("Успешный вход")
    @allure.description("POST /api/auth/login с form-данными возвращает 200 и тело по схеме Token")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.positive
    def test_login_valid(self, session, registered_user):
        with allure.step("Логин зарегистрированным пользователем, проверка тела ответа по схеме Token"):
            logger.info("Логин зарегистрированным пользователем, проверка тела ответа по схеме Token")
            creds = registered_user["request"]
            response = session.post(Routes.LOGIN, data={"username": creds["email"], "password": creds["password"]})

            assert response.status_code == 200, response.text
            token = Token.model_validate(response.json())
            assert token.token_type == "bearer", "token_type в ответе не 'bearer'"
            assert token.access_token, "access_token в ответе пустой"

    @allure.epic("NewsPlatform")
    @allure.feature("Авторизация")
    @allure.story("Вход с неверным паролем")
    @allure.description("Верный email и неверный пароль возвращают 401 и detail 'Incorrect email or password'")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_login_wrong_password(self, session, registered_user):
        with allure.step("Логин верным email и неверным паролем, ожидаем 401"):
            logger.info("Логин верным email и неверным паролем, ожидаем 401")
            email = registered_user["request"]["email"]
            response = session.post(Routes.LOGIN, data={"username": email, "password": "wrong-pass"})

            assert response.status_code == 401, response.text
            assert response.json()["detail"] == WRONG_CREDENTIALS_DETAIL, "Текст detail не совпал с ожидаемым"

    @allure.epic("NewsPlatform")
    @allure.feature("Авторизация")
    @allure.story("Вход несуществующим email")
    @allure.description("Незарегистрированный email возвращает 401 и detail 'Incorrect email or password'")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_login_nonexistent_email(self, session, user_data):
        with allure.step("Логин незарегистрированным email, ожидаем 401"):
            logger.info("Логин незарегистрированным email, ожидаем 401")
            response = session.post(Routes.LOGIN, data={"username": user_data["email"], "password": user_data["password"]})

            assert response.status_code == 401, response.text
            assert response.json()["detail"] == WRONG_CREDENTIALS_DETAIL, "Текст detail не совпал с ожидаемым"

    @allure.epic("NewsPlatform")
    @allure.feature("Авторизация")
    @allure.story("Вход с некорректным email")
    @allure.description("username без @ возвращает 401 и detail с сообщением об ошибке")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_login_malformed_email(self, session):
        with allure.step("Логин username без @, ожидаем 401"):
            logger.info("Логин username без @, ожидаем 401")
            response = session.post(Routes.LOGIN, data={"username": "example", "password": "whatever"})

            assert response.status_code == 401, response.text
            assert response.json()["detail"] == WRONG_CREDENTIALS_DETAIL, "Текст detail не совпал с ожидаемым"

    @allure.epic("NewsPlatform")
    @allure.feature("Авторизация")
    @allure.story("Пустое обязательное поле формы логина")
    @allure.description("POST /api/auth/login без обязательного поля формы возвращает 422, поле присутствует в detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.parametrize("field", ["username", "password"])
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_login_missing_field(self, session, registered_user, field):
        with allure.step(f"Логин без обязательного поля {field}, ожидаем 422"):
            logger.info(f"Логин без обязательного поля {field}, ожидаем 422")
            creds = registered_user["request"]
            data = {"username": creds["email"], "password": creds["password"]}
            del data[field]
            response = session.post(Routes.LOGIN, data=data)

            assert response.status_code == 422, response.text
            err = ValidationErrorResponse.model_validate(response.json())
            assert any(field in item.loc for item in err.detail), f"Поля {field} нет в detail ответа"

    @allure.epic("NewsPlatform")
    @allure.feature("Авторизация")
    @allure.story("Логин с телом JSON вместо формы")
    @allure.description("POST /api/auth/login ожидает x-www-form-urlencoded, тело JSON возвращает 422")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_login_json_instead_of_form(self, session, registered_user):
        with allure.step("Логин телом JSON вместо формы, ожидаем 422"):
            logger.info("Логин телом JSON вместо формы, ожидаем 422")
            creds = registered_user["request"]
            response = session.post(Routes.LOGIN, json={"username": creds["email"], "password": creds["password"]})

            assert response.status_code == 422, response.text
