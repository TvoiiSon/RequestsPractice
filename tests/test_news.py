import pytest
import allure
from loguru import logger
from pydantic import TypeAdapter
from helpers.constants import MISSING_ID, NON_NUMERIC_ID
from helpers.routes import Routes
from models.common import Page, ValidationErrorResponse
from models.news import NewsResponse, TagResponse

class TestNews:
    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Создание новости без изображения")
    @allure.description("POST /api/news/ с обязательными полями создаёт новость, ответ по схеме NewsResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.positive
    def test_create_news_without_image(self, auth_session, article_data):
        with allure.step("Создание новости без image, проверка тела ответа по схеме NewsResponse"):
            logger.info("Создание новости без image, проверка тела ответа по схеме NewsResponse")
            response = auth_session.post(Routes.NEWS, data=article_data)

            assert response.status_code == 200, response.text
            news = NewsResponse.model_validate(response.json())
            assert news.title == article_data["title"], "title в ответе не совпал с отправленным"
            assert news.text == article_data["text"], "text в ответе не совпал с отправленным"
            assert news.image_path is None, "image_path должен быть null, если изображение не передано"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Создание новости с изображением")
    @allure.description("POST /api/news/ с файлом image возвращает новость с непустым image_path")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.positive
    def test_create_news_with_image(self, auth_session, article_data, image_file):
        with allure.step("Создание новости с файлом image, проверка непустого image_path"):
            logger.info("Создание новости с файлом image, проверка непустого image_path")
            response = auth_session.post(Routes.NEWS, data=article_data, files={"image": image_file})

            assert response.status_code == 200, response.text
            news = NewsResponse.model_validate(response.json())
            assert news.title == article_data["title"], "title в ответе не совпал с отправленным"
            assert news.image_path is not None, "image_path должен быть заполнен после загрузки изображения"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Получение списка всех новостей")
    @allure.description("GET /api/news/ возвращает страницу items/total/page/per_page/total_pages")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.positive
    def test_get_all_news(self, session, created_news):
        with allure.step("Получение списка новостей, проверка структуры страницы"):
            logger.info("Получение списка новостей, проверка структуры страницы")
            response = session.get(Routes.NEWS)

            assert response.status_code == 200, response.text
            page = Page[NewsResponse].model_validate(response.json())
            assert page.total >= 1, "Список новостей пуст, хотя новость только что создана"
            assert len(page.items) <= page.per_page, "Элементов на странице больше per_page"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Список новостей с фильтрами")
    @allure.description("GET /api/news/ учитывает query-параметры page, per_page, tag, search")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.positive
    def test_get_news_with_filters(self, session, created_news):
        with allure.step("Получение списка новостей с фильтрами page/per_page/tag/search"):
            logger.info("Получение списка новостей с фильтрами page/per_page/tag/search")
            per_page = 5
            params = {"page": 1, "per_page": per_page, "search": created_news["title"].split()[0]}
            if created_news["tags"]:
                params["tag"] = created_news["tags"][0]["name"]

            response = session.get(Routes.NEWS, params=params)

            assert response.status_code == 200, response.text
            page = Page[NewsResponse].model_validate(response.json())
            assert page.page == 1, "page в ответе не совпал с запрошенным"
            assert page.per_page == per_page, "per_page в ответе не совпал с запрошенным"
            assert len(page.items) <= per_page, "Элементов на странице больше per_page"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Детальная информация о новости по ID")
    @allure.description("GET /api/news/{news_id} возвращает ту же новость по схеме NewsResponse")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.tag("Позитивный")
    @pytest.mark.smoke
    @pytest.mark.api
    @pytest.mark.positive
    def test_get_news_by_id(self, session, created_news):
        with allure.step("Получение новости по id, проверка совпадения id и title"):
            logger.info("Получение новости по id, проверка совпадения id и title")
            news_id = created_news["id"]
            response = session.get(Routes.news_item(news_id))

            assert response.status_code == 200, response.text
            news = NewsResponse.model_validate(response.json())
            assert news.id == news_id, "id в ответе не совпал с запрошенным"
            assert news.title == created_news["title"], "title в ответе не совпал с созданной новостью"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Получение списка всех тегов")
    @allure.description("GET /api/news/tags возвращает массив TagResponse")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Позитивный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.positive
    def test_get_all_tags(self, session, created_news):
        with allure.step("Получение списка тегов, проверка каждого элемента по схеме TagResponse"):
            logger.info("Получение списка тегов, проверка каждого элемента по схеме TagResponse")
            response = session.get(Routes.NEWS_TAGS)

            assert response.status_code == 200, response.text
            tags = TypeAdapter(list[TagResponse]).validate_python(response.json())
            assert len(tags) >= 1, "Список тегов пуст, хотя новость с тегами только что создана"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Создание новости без токена")
    @allure.description("POST /api/news/ без Authorization отклоняется с 401")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_news_unauthorized(self, session, article_data):
        with allure.step("Создание новости без токена, ожидаем 401"):
            logger.info("Создание новости без токена, ожидаем 401")
            response = session.post(Routes.NEWS, data=article_data)

            assert response.status_code == 401, response.text

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Создание новости с невалидным токеном")
    @allure.description("POST /api/news/ с недействительным Bearer-токеном отклоняется с 401")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_news_invalid_token(self, bad_token_session, article_data):
        with allure.step("Создание новости с невалидным токеном, ожидаем 401"):
            logger.info("Создание новости с невалидным токеном, ожидаем 401")
            response = bad_token_session.post(Routes.NEWS, data=article_data)

            assert response.status_code == 401, response.text

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Создание новости без обязательного поля")
    @allure.description("POST /api/news/ без title или text возвращает 422, поле присутствует в detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.parametrize("field", ["title", "text"])
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_create_news_missing_required_field(self, auth_session, article_data, field):
        with allure.step(f"Создание новости без обязательного поля {field}, ожидаем 422"):
            logger.info(f"Создание новости без обязательного поля {field}, ожидаем 422")
            del article_data[field]
            response = auth_session.post(Routes.NEWS, data=article_data)

            assert response.status_code == 422, response.text
            err = ValidationErrorResponse.model_validate(response.json())
            assert any(field in item.loc for item in err.detail), f"Поля {field} нет в detail ответа"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Новость по несуществующему ID")
    @allure.description("GET /api/news/{news_id} с несуществующим id возвращает 404 с detail")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_get_news_by_id_not_found(self, session):
        with allure.step("Получение новости по несуществующему id, ожидаем 404"):
            logger.info("Получение новости по несуществующему id, ожидаем 404")
            response = session.get(Routes.news_item(MISSING_ID))

            assert response.status_code == 404, response.text
            assert "detail" in response.json(), "В ответе нет detail с описанием ошибки"

    @allure.epic("NewsPlatform")
    @allure.feature("Новости")
    @allure.story("Новость по нечисловому ID")
    @allure.description("GET /api/news/{news_id} с нечисловым id возвращает 422")
    @allure.severity(allure.severity_level.MINOR)
    @allure.tag("Негативный")
    @pytest.mark.regression
    @pytest.mark.api
    @pytest.mark.negative
    def test_get_news_by_id_invalid_type(self, session):
        with allure.step("Получение новости по нечисловому id, ожидаем 422"):
            logger.info("Получение новости по нечисловому id, ожидаем 422")
            response = session.get(Routes.news_item(NON_NUMERIC_ID))

            assert response.status_code == 422, response.text
