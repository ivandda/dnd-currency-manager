from app.database.database import SessionLocal


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
