import allure
import pytest
from pydantic import TypeAdapter

from models.comments import CommentResponse
from models.common import ValidationErrorResponse
from helpers.data_generator import generate_comment


@allure.epic("News")
@allure.feature("Comments")
class TestComments:

    # ---------- позитивные ----------

    @allure.title("Создание комментария к новости → 200")
    @allure.story("Создание комментария")
    @allure.description("POST /api/news/{news_id}/comments с телом {text}; ответ по схеме CommentResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_create_comment(self, auth_session, created_news):
        news_id = created_news["id"]
        text = generate_comment()
        resp = auth_session.post(f"/api/news/{news_id}/comments", json={"text": text})

        assert resp.status_code == 200, resp.text
        comment = CommentResponse.model_validate(resp.json())
        assert comment.text == text

    @allure.title("Получение списка комментариев к новости → 200")
    @allure.story("Чтение комментариев")
    @allure.description("GET /api/news/{news_id}/comments возвращает массив CommentResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_get_comments(self, auth_session, created_news):
        news_id = created_news["id"]
        text = generate_comment()
        auth_session.post(f"/api/news/{news_id}/comments", json={"text": text})

        resp = auth_session.get(f"/api/news/{news_id}/comments")

        assert resp.status_code == 200, resp.text
        comments = TypeAdapter(list[CommentResponse]).validate_python(resp.json())
        assert any(c.text == text for c in comments)

    # ---------- негативные ----------

    @allure.title("Создание комментария без токена → 401")
    @allure.story("Создание комментария")
    @allure.description("POST /api/news/{news_id}/comments без Authorization отклоняется")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_comment_unauthorized(self, session, created_news):
        resp = session.post(f"/api/news/{created_news['id']}/comments", json={"text": "hi"})

        assert resp.status_code == 401, resp.text

    @allure.title("Создание комментария с невалидным токеном → 401")
    @allure.story("Создание комментария")
    @allure.description("POST /api/news/{news_id}/comments с 'Bearer <мусор>' отклоняется")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_comment_invalid_token(self, bad_token_session, created_news):
        resp = bad_token_session.post(f"/api/news/{created_news['id']}/comments", json={"text": "hi"})

        assert resp.status_code == 401, resp.text

    @allure.title("Создание комментария без поля text → 422")
    @allure.story("Создание комментария")
    @allure.description("POST /api/news/{news_id}/comments без text возвращает 422; поле есть в detail[*].loc")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_comment_missing_text(self, auth_session, created_news):
        resp = auth_session.post(f"/api/news/{created_news['id']}/comments", json={})

        assert resp.status_code == 422, resp.text
        err = ValidationErrorResponse.model_validate(resp.json())
        assert any("text" in item.loc for item in err.detail)

    @allure.title("Комментарий к несуществующей новости → 404")
    @allure.story("Создание комментария")
    @allure.description("POST /api/news/{news_id}/comments с несуществующим news_id возвращает 404")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_comment_news_not_found(self, auth_session):
        resp = auth_session.post("/api/news/99999999/comments", json={"text": generate_comment()})

        assert resp.status_code == 404, resp.text

    @allure.title("Список комментариев несуществующей новости → 404")
    @allure.story("Чтение комментариев")
    @allure.description("GET /api/news/{news_id}/comments с несуществующим news_id возвращает 404")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_get_comments_news_not_found(self, session):
        resp = session.get("/api/news/99999999/comments")

        assert resp.status_code == 404, resp.text

    @allure.title("Комментарий к новости с нечисловым ID → 422")
    @allure.story("Создание комментария")
    @allure.description("POST /api/news/{news_id}/comments с нечисловым news_id возвращает 422")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_comment_invalid_news_id_type(self, auth_session):
        resp = auth_session.post("/api/news/not-a-number/comments", json={"text": "x"})

        assert resp.status_code == 422, resp.text
