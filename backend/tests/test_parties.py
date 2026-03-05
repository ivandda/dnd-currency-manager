"""Tests for party management endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.user import User
from app.models.party import Party
from app.models.character import Character


class TestCreateParty:
    """Test party creation."""

    def test_create_party(self, client: TestClient, dm_headers: dict):
        response = client.post(
            "/api/parties",
            json={"name": "Dragon Slayers"},
            headers=dm_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Dragon Slayers"
        assert len(data["code"]) == 4
        assert data["is_active"] is True
        assert data["use_gold"] is True
        assert data["use_electrum"] is False

    def test_create_party_custom_coins(self, client: TestClient, dm_headers: dict):
        response = client.post(
            "/api/parties",
            json={
                "name": "Rich Campaign",
                "use_platinum": True,
                "use_electrum": True,
            },
            headers=dm_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["use_platinum"] is True
        assert data["use_electrum"] is True

    def test_create_party_unauthenticated(self, client: TestClient):
        response = client.post(
            "/api/parties",
            json={"name": "No Auth Party"},
        )
        assert response.status_code == 401


class TestJoinParty:
    """Test joining a party."""

    def test_join_party(
        self, client: TestClient, auth_headers: dict, test_party: Party
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/join",
            json={"character_name": "Legolas", "character_class": "Ranger"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Legolas"
        assert data["character_class"] == "Ranger"
        assert data["balance_cp"] == 0

    def test_join_party_dm_cannot_join_own(
        self, client: TestClient, dm_headers: dict, test_party: Party
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/join",
            json={"character_name": "DM Char", "character_class": "God"},
            headers=dm_headers,
        )
        assert response.status_code == 400
        assert "DM cannot join" in response.json()["detail"]

    def test_join_party_duplicate(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/join",
            json={"character_name": "Duplicate", "character_class": "Thief"},
            headers=auth_headers,
        )
        assert response.status_code == 409

    def test_join_nonexistent_party(self, client: TestClient, auth_headers: dict):
        response = client.post(
            "/api/parties/XXXX/join",
            json={"character_name": "Lost", "character_class": "Wanderer"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestPartyDetail:
    """Test getting party details."""

    def test_get_party_as_dm(
        self, client: TestClient, dm_headers: dict, test_party: Party
    ):
        response = client.get(
            f"/api/parties/{test_party.code}", headers=dm_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Party"
        assert data["dm_username"] == "testdm"

    def test_get_party_as_member(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.get(
            f"/api/parties/{test_party.code}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["characters"]) >= 1

    def test_get_party_non_member(
        self,
        client: TestClient,
        second_auth_headers: dict,
        test_party: Party,
        second_user: User,
    ):
        response = client.get(
            f"/api/parties/{test_party.code}", headers=second_auth_headers
        )
        assert response.status_code == 403


class TestLeaveParty:
    """Test leaving a party."""

    def test_leave_party(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/leave", headers=auth_headers
        )
        assert response.status_code == 200
        assert "left the party" in response.json()["message"]

    def test_leave_party_no_character(
        self, client: TestClient, auth_headers: dict, test_party: Party
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/leave", headers=auth_headers
        )
        assert response.status_code == 404


class TestKickCharacter:
    """Test kicking a character from a party."""

    def test_kick_character(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/kick",
            json={"character_id": test_character.id},
            headers=dm_headers,
        )
        assert response.status_code == 200
        assert "kicked" in response.json()["message"]

    def test_kick_not_dm(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/kick",
            json={"character_id": test_character.id},
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestArchiveParty:
    """Test archiving a party."""

    def test_archive_party(
        self, client: TestClient, dm_headers: dict, test_party: Party
    ):
        response = client.patch(
            f"/api/parties/{test_party.code}/archive", headers=dm_headers
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

    def test_archive_not_dm(
        self, client: TestClient, auth_headers: dict, test_party: Party
    ):
        response = client.patch(
            f"/api/parties/{test_party.code}/archive", headers=auth_headers
        )
        assert response.status_code == 403


class TestListParties:
    """Test listing parties."""

    def test_list_as_dm(
        self, client: TestClient, dm_headers: dict, test_party: Party
    ):
        response = client.get("/api/parties", headers=dm_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_as_player(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.get("/api/parties", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
