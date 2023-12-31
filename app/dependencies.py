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
        "name": "auth",
        "description": "Authentication: login and register",
    },
    {
        "name": "characters",
        "description": "Characters: create and get info",
    },
    {
        "name": "parties",
        "description": "Parties: create, get info, add characters, assign DM",
    },
    {
        "name": "money characters",
        "description": "Money operations characters can do",
    },
    {
        "name": "money dm",
        "description": "Money operations only a DM of a party can do",
    },
    {
        "name": "money parties",
        "description": "Money operations only party leader con do",
    }
]

# more swagger_ui_parameters :https://swagger.io/docs/open-source-tools/swagger-ui/usage/configuration/
swagger_ui_parameters = {"filter": True,
                         # "operationsSorter": "method"
                         }
