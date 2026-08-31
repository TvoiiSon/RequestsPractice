import pytest
import allure
from loguru import logger
from pydantic import TypeAdapter
from helpers.constants import MISSING_ID, NON_NUMERIC_ID
from helpers.data_generator import generate_comment
from helpers.routes import Routes
from models.comments import CommentResponse
from models.common import ValidationErrorResponse

class TestComments:
    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Создание комментария к новости")
    @allure.description("POST /api/news/{news_id}/comments с телом text создаёт комментарий по схеме CommentResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.positive
    def test_create_comment(self, created_news, add_comment):
        with allure.step("Создание комментария к новости, проверка тела ответа по схеме CommentResponse"):
            logger.info("Создание комментария к новости, проверка тела ответа по схеме CommentResponse")
            text, response = add_comment(created_news["id"])

            assert response.status_code == 200, response.text
            comment = CommentResponse.model_validate(response.json())
            assert comment.text == text, "text в ответе не совпал с отправленным"

    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Получение списка комментариев к новости")
    @allure.description("GET /api/news/{news_id}/comments возвращает массив CommentResponse с добавленным комментарием")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.positive
    def test_get_comments(self, session, created_news, add_comment):
        with allure.step("Добавление комментария и получение списка комментариев новости"):
            logger.info("Добавление комментария и получение списка комментариев новости")
            news_id = created_news["id"]
            text, _ = add_comment(news_id)

            response = session.get(Routes.news_comments(news_id))

            assert response.status_code == 200, response.text
            comments = TypeAdapter(list[CommentResponse]).validate_python(response.json())
            assert any(c.text == text for c in comments), "Добавленный комментарий не найден в списке"

    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Создание комментария без токена")
    @allure.description("POST /api/news/{news_id}/comments без Authorization отклоняется с 401")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_comment_unauthorized(self, session, created_news):
        with allure.step("Создание комментария без токена, ожидаем 401"):
            logger.info("Создание комментария без токена, ожидаем 401")
            response = session.post(Routes.news_comments(created_news["id"]), json={"text": generate_comment()})

            assert response.status_code == 401, response.text

    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Создание комментария с невалидным токеном")
    @allure.description("POST /api/news/{news_id}/comments с недействительным Bearer-токеном отклоняется с 401")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_comment_invalid_token(self, bad_token_session, created_news):
        with allure.step("Создание комментария с невалидным токеном, ожидаем 401"):
            logger.info("Создание комментария с невалидным токеном, ожидаем 401")
            response = bad_token_session.post(Routes.news_comments(created_news["id"]), json={"text": generate_comment()})

            assert response.status_code == 401, response.text

    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Создание комментария без поля text")
    @allure.description("POST /api/news/{news_id}/comments без text возвращает 422, поле присутствует в detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_comment_missing_text(self, auth_session, created_news):
        with allure.step("Создание комментария без поля text, ожидаем 422"):
            logger.info("Создание комментария без поля text, ожидаем 422")
            response = auth_session.post(Routes.news_comments(created_news["id"]), json={})

            assert response.status_code == 422, response.text
            err = ValidationErrorResponse.model_validate(response.json())
            assert any("text" in item.loc for item in err.detail), "Поля text нет в detail ответа"

    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Комментарий к несуществующей новости")
    @allure.description("POST /api/news/{news_id}/comments с несуществующим news_id возвращает 404")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_comment_news_not_found(self, auth_session):
        with allure.step("Создание комментария к несуществующей новости, ожидаем 404"):
            logger.info("Создание комментария к несуществующей новости, ожидаем 404")
            response = auth_session.post(Routes.news_comments(MISSING_ID), json={"text": generate_comment()})

            assert response.status_code == 404, response.text

    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Список комментариев несуществующей новости")
    @allure.description("GET /api/news/{news_id}/comments с несуществующим news_id возвращает 404")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_get_comments_news_not_found(self, session):
        with allure.step("Получение комментариев несуществующей новости, ожидаем 404"):
            logger.info("Получение комментариев несуществующей новости, ожидаем 404")
            response = session.get(Routes.news_comments(MISSING_ID))

            assert response.status_code == 404, response.text

    @allure.epic("NewsPlatform")
    @allure.feature("Комментарии")
    @allure.story("Комментарий к новости с нечисловым ID")
    @allure.description("POST /api/news/{news_id}/comments с нечисловым news_id возвращает 422")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_comment_invalid_news_id_type(self, auth_session):
        with allure.step("Создание комментария к новости с нечисловым id, ожидаем 422"):
            logger.info("Создание комментария к новости с нечисловым id, ожидаем 422")
            response = auth_session.post(Routes.news_comments(NON_NUMERIC_ID), json={"text": generate_comment()})

            assert response.status_code == 422, response.text
