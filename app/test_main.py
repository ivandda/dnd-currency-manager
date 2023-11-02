from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home():
    response = client.get("/home")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the home page!"}


def test_get_characters():
    response = client.get("/characters/")
    assert response.status_code == 200


def test_error_get_one_character():
    response = client.get("/characters/99999999999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Character with id 99999999999999 not found"}


def test_error_get_all_parties():
    response = client.get("/parties/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_error_get_one_party():
    response = client.get("/parties/99999999999999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
