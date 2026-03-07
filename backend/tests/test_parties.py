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


class TestMyCoinSettings:
    """Test per-user-per-party coin settings."""

    def test_member_can_update_own_coin_settings(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.patch(
            f"/api/parties/{test_party.code}/my-coins",
            json={"use_gold": False, "use_electrum": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["use_gold"] is False
        assert data["use_electrum"] is True
        assert data["use_platinum"] is False

    def test_dm_can_update_own_coin_settings_without_character(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
    ):
        response = client.patch(
            f"/api/parties/{test_party.code}/my-coins",
            json={"use_platinum": True},
            headers=dm_headers,
        )
        assert response.status_code == 200
        assert response.json()["use_platinum"] is True

    def test_non_member_cannot_update_coin_settings(
        self,
        client: TestClient,
        second_auth_headers: dict,
        test_party: Party,
    ):
        response = client.patch(
            f"/api/parties/{test_party.code}/my-coins",
            json={"use_gold": False},
            headers=second_auth_headers,
        )
        assert response.status_code == 403

    def test_settings_are_isolated_per_user(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        update = client.patch(
            f"/api/parties/{test_party.code}/my-coins",
            json={"use_gold": False, "use_platinum": True},
            headers=auth_headers,
        )
        assert update.status_code == 200

        me_detail = client.get(f"/api/parties/{test_party.code}", headers=auth_headers)
        other_detail = client.get(f"/api/parties/{test_party.code}", headers=second_auth_headers)
        assert me_detail.status_code == 200
        assert other_detail.status_code == 200

        assert me_detail.json()["my_coin_settings"] == {
            "use_gold": False,
            "use_electrum": False,
            "use_platinum": True,
        }
        assert other_detail.json()["my_coin_settings"] == {
            "use_gold": True,
            "use_electrum": False,
            "use_platinum": False,
        }

    def test_settings_are_isolated_per_party(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        test_user: User,
        test_dm: User,
        session: Session,
    ):
        update = client.patch(
            f"/api/parties/{test_party.code}/my-coins",
            json={"use_gold": False, "use_platinum": True},
            headers=auth_headers,
        )
        assert update.status_code == 200

        second_party = Party(
            name="Second Party",
            code="AB12",
            dm_id=test_dm.id,
        )
        session.add(second_party)
        session.commit()
        session.refresh(second_party)

        second_char = Character(
            name="Bilbo",
            character_class="Rogue",
            user_id=test_user.id,
            party_id=second_party.id,
            balance_cp=100,
        )
        session.add(second_char)
        session.commit()

        second_detail = client.get(f"/api/parties/{second_party.code}", headers=auth_headers)
        assert second_detail.status_code == 200
        assert second_detail.json()["my_coin_settings"] == {
            "use_gold": True,
            "use_electrum": False,
            "use_platinum": False,
        }


class TestBalanceVisibility:
    """Test per-character balance visibility in party detail."""

    def test_default_balance_is_public(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.get(f"/api/parties/{test_party.code}", headers=auth_headers)
        assert response.status_code == 200
        me = next(c for c in response.json()["characters"] if c["id"] == test_character.id)
        assert me["is_balance_public"] is True
        assert me["balance_visible_to_viewer"] is True

    def test_player_can_toggle_own_balance_visibility(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.patch(
            f"/api/parties/{test_party.code}/my-character-settings",
            json={"is_balance_public": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_balance_public"] is False

    def test_other_players_cannot_see_hidden_balance(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        hide = client.patch(
            f"/api/parties/{test_party.code}/my-character-settings",
            json={"is_balance_public": False},
            headers=auth_headers,
        )
        assert hide.status_code == 200

        response = client.get(f"/api/parties/{test_party.code}", headers=second_auth_headers)
        assert response.status_code == 200
        hidden_char = next(c for c in response.json()["characters"] if c["id"] == test_character.id)
        assert hidden_char["balance_visible_to_viewer"] is False
        assert hidden_char["balance_cp"] == 0
        assert hidden_char["balance_display"] == {"cp": 0}

    def test_owner_still_sees_own_hidden_balance(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        hide = client.patch(
            f"/api/parties/{test_party.code}/my-character-settings",
            json={"is_balance_public": False},
            headers=auth_headers,
        )
        assert hide.status_code == 200

        response = client.get(f"/api/parties/{test_party.code}", headers=auth_headers)
        assert response.status_code == 200
        me = next(c for c in response.json()["characters"] if c["id"] == test_character.id)
        assert me["balance_visible_to_viewer"] is True
        assert me["balance_cp"] == 10000

    def test_dm_always_sees_hidden_balances(
        self,
        client: TestClient,
        auth_headers: dict,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        hide = client.patch(
            f"/api/parties/{test_party.code}/my-character-settings",
            json={"is_balance_public": False},
            headers=auth_headers,
        )
        assert hide.status_code == 200

        response = client.get(f"/api/parties/{test_party.code}", headers=dm_headers)
        assert response.status_code == 200
        char_data = next(c for c in response.json()["characters"] if c["id"] == test_character.id)
        assert char_data["balance_visible_to_viewer"] is True
        assert char_data["balance_cp"] == 10000

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
