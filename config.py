import os

BASE_URL = os.getenv("BASE_URL", "https://archiscope.ru")

# Токен администратора для очистки тестовых данных после прогона.
# Если не задан - фикстуры не пытаются удалять созданные сущности
# (у API нет публичных DELETE-эндпоинтов).
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
