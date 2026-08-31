from faker import Faker

fake = Faker("ru_RU")

def generate_user() -> dict:
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "password": fake.password(length=12),
        "phone": fake.phone_number(),
    }

def generate_comment() -> str:
    return fake.unique.sentence()

def generate_article() -> dict:
    return {
        "title": fake.unique.sentence(),
        "subtitle": fake.unique.sentence(),
        "text": fake.unique.sentence(),
        "tags": ", ".join(fake.words(nb=3)),
    }

def generate_user_response() -> dict:
    user = generate_user()
    return {
        "id": fake.random_int(1, 10_000),
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone": None,
        "photo_path": None,
        "created_at": fake.date_time_this_year().isoformat(),
    }
