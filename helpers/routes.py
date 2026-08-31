class Routes:
    # auth
    REGISTER = "/api/auth/register"
    LOGIN = "/api/auth/login"

    # users/me
    USERS_ME = "/api/users/me"
    USERS_ME_PHOTO = "/api/users/me/photo"

    # news
    NEWS = "/api/news/"
    NEWS_TAGS = "/api/news/tags"

    # admin
    ADMIN_USERS = "/api/admin/users"
    ADMIN_STATS = "/api/admin/stats"

    @staticmethod
    def news_item(news_id) -> str:
        return f"/api/news/{news_id}"

    @staticmethod
    def news_comments(news_id) -> str:
        return f"/api/news/{news_id}/comments"

    @staticmethod
    def admin_news(news_id) -> str:
        return f"/api/admin/news/{news_id}"

    @staticmethod
    def admin_user(user_id) -> str:
        return f"/api/admin/users/{user_id}"

    @staticmethod
    def admin_user_toggle(user_id) -> str:
        return f"/api/admin/users/{user_id}/toggle-active"
