from enum import Enum

from app.database.database import SessionLocal


# Currency Values
class Currencies(int, Enum):
    platinum = 1000
    gold = 100
    electrum = 50
    silver = 10
    copper = 1


values = {currency.name: currency.value for currency in Currencies}
currency_types = [currency.name for currency in Currencies]


# Database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Swagger parameters

tags_metadata = [
    {
        "name": "characters",
        "description": "Operations with characters.",
    },
    {
        "name": "party",
        "description": "Operations with parties.",
    },
    {
        "name": "character transactions",
        "description": "Transaction between characters and currency info.",
    },

    {
        "name": "party transactions",
        "description": "Transaction between parties and currency info.",
    },
    {
        "name": "home",
        "description": "Home page.",
    },
]

# more swagger_ui_parameters :https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
swagger_ui_parameters = {"filter": True,
                         "operationsSorter": "method"}
