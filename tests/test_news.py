import allure
import pytest
from pydantic import TypeAdapter

from helpers.constants import MISSING_ID, NON_NUMERIC_ID
from helpers.routes import Routes
from models.common import Page, ValidationErrorResponse
from models.news import NewsResponse, TagResponse


@allure.epic("News")
@allure.feature("News")
class TestNews:

    @allure.title("Создание новости без изображения → 200")
    @allure.story("Создание новости")
    @allure.description("POST /api/news/ с обязательными полями создаёт новость; ответ по схеме NewsResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_create_news_without_image(self, auth_session, article_data):
        resp = auth_session.post(Routes.NEWS, data=article_data)

        assert resp.status_code == 200, resp.text
        news = NewsResponse.model_validate(resp.json())
        assert news.title == article_data["title"]
        assert news.text == article_data["text"]
        assert news.image_path is None

    @allure.title("Создание новости с изображением → 200")
    @allure.story("Создание новости")
    @allure.description("POST /api/news/ с файлом image возвращает новость с непустым image_path")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.positive
    def test_create_news_with_image(self, auth_session, article_data, news_image):
        resp = auth_session.post(Routes.NEWS, data=article_data, files={"image": news_image})

        assert resp.status_code == 200, resp.text
        news = NewsResponse.model_validate(resp.json())
        assert news.title == article_data["title"]
        assert news.image_path is not None

    @allure.title("Получение списка всех новостей → 200")
    @allure.story("Чтение новостей")
    @allure.description("GET /api/news/ возвращает страницу items/total/page/per_page/total_pages")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_get_all_news(self, session, created_news):
        resp = session.get(Routes.NEWS)

        assert resp.status_code == 200, resp.text
        page = Page[NewsResponse].model_validate(resp.json())
        assert page.total >= 1
        assert len(page.items) <= page.per_page

    @allure.title("Список новостей с фильтрами page/per_page/tag/search → 200")
    @allure.story("Чтение новостей")
    @allure.description("GET /api/news/ учитывает query-параметры пагинации и фильтрации")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.positive
    def test_get_news_with_filters(self, session, created_news):
        per_page = 5
        params = {
            "page": 1,
            "per_page": per_page,
            "search": created_news["title"].split()[0],
        }
        if created_news["tags"]:
            params["tag"] = created_news["tags"][0]["name"]

        resp = session.get(Routes.NEWS, params=params)

        assert resp.status_code == 200, resp.text
        page = Page[NewsResponse].model_validate(resp.json())
        assert page.page == 1
        assert page.per_page == per_page
        assert len(page.items) <= per_page

    @allure.title("Детальная информация о новости по ID → 200")
    @allure.story("Чтение новостей")
    @allure.description("GET /api/news/{news_id} возвращает ту же новость")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.positive
    def test_get_news_by_id(self, session, created_news):
        news_id = created_news["id"]
        resp = session.get(Routes.news_item(news_id))

        assert resp.status_code == 200, resp.text
        news = NewsResponse.model_validate(resp.json())
        assert news.id == news_id
        assert news.title == created_news["title"]

    @allure.title("Получение списка всех тегов → 200")
    @allure.story("Теги")
    @allure.description("GET /api/news/tags возвращает массив TagResponse")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.positive
    def test_get_all_tags(self, session, created_news):
        resp = session.get(Routes.NEWS_TAGS)

        assert resp.status_code == 200, resp.text
        tags = TypeAdapter(list[TagResponse]).validate_python(resp.json())
        assert len(tags) >= 1

    @allure.title("Создание новости без токена → 401")
    @allure.story("Создание новости")
    @allure.description("POST /api/news/ без Authorization отклоняется")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_news_unauthorized(self, session, article_data):
        resp = session.post(Routes.NEWS, data=article_data)

        assert resp.status_code == 401, resp.text

    @allure.title("Создание новости с невалидным токеном → 401")
    @allure.story("Создание новости")
    @allure.description("POST /api/news/ с 'Bearer <мусор>' отклоняется")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_create_news_invalid_token(self, bad_token_session, article_data):
        resp = bad_token_session.post(Routes.NEWS, data=article_data)

        assert resp.status_code == 401, resp.text

    @allure.title("Создание новости без обязательного поля {field} → 422")
    @allure.story("Создание новости")
    @allure.description("POST /api/news/ без title/text возвращает 422; поле есть в detail[*].loc")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    @pytest.mark.parametrize("field", ["title", "text"])
    def test_create_news_missing_required_field(self, auth_session, article_data, field):
        del article_data[field]
        resp = auth_session.post(Routes.NEWS, data=article_data)

        assert resp.status_code == 422, resp.text
        err = ValidationErrorResponse.model_validate(resp.json())
        assert any(field in item.loc for item in err.detail)

    @allure.title("Новость по несуществующему ID → 404")
    @allure.story("Чтение новостей")
    @allure.description("GET /api/news/{news_id} с несуществующим id возвращает 404 с detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_get_news_by_id_not_found(self, session):
        resp = session.get(Routes.news_item(MISSING_ID))

        assert resp.status_code == 404, resp.text
        assert "detail" in resp.json()

    @allure.title("Новость по нечисловому ID → 422")
    @allure.story("Чтение новостей")
    @allure.description("GET /api/news/{news_id} с нечисловым id возвращает 422")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.negative
    def test_get_news_by_id_invalid_type(self, session):
        resp = session.get(Routes.news_item(NON_NUMERIC_ID))

        assert resp.status_code == 422, resp.text
