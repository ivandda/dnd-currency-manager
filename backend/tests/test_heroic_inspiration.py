"""Tests for Heroic Inspiration endpoints."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.events import event_manager
from app.models.character import Character
from app.models.party import Party


class TestHeroicInspiration:
    """Test Heroic Inspiration grant, revoke, and use flows."""

    def test_dm_can_grant_heroic_inspiration(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/grant",
            headers=dm_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "granted"
        assert data["character_id"] == test_character.id
        assert data["has_heroic_inspiration"] is True
        assert data["target_user_id"] == test_character.user_id

        session.refresh(test_character)
        assert test_character.has_heroic_inspiration is True

    def test_dm_can_revoke_heroic_inspiration(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        test_character.has_heroic_inspiration = True
        session.add(test_character)
        session.commit()

        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/revoke",
            headers=dm_headers,
        )

        assert response.status_code == 200
        assert response.json()["action"] == "revoked"

        session.refresh(test_character)
        assert test_character.has_heroic_inspiration is False

    def test_player_can_use_own_heroic_inspiration(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        test_character.has_heroic_inspiration = True
        session.add(test_character)
        session.commit()

        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/use",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "used"
        assert data["has_heroic_inspiration"] is False
        assert data["actor_user_id"] == test_character.user_id

        session.refresh(test_character)
        assert test_character.has_heroic_inspiration is False

    def test_player_cannot_grant_heroic_inspiration(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/grant",
            headers=auth_headers,
        )

        assert response.status_code == 403

    def test_player_cannot_revoke_heroic_inspiration(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/revoke",
            headers=auth_headers,
        )

        assert response.status_code == 403

    def test_player_cannot_use_another_players_heroic_inspiration(
        self,
        client: TestClient,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        test_character.has_heroic_inspiration = True
        second_character.has_heroic_inspiration = False
        session.add(test_character)
        session.add(second_character)
        session.commit()

        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/use",
            headers=second_auth_headers,
        )

        assert response.status_code == 409
        assert "do not have Heroic Inspiration" in response.json()["detail"]

        session.refresh(test_character)
        assert test_character.has_heroic_inspiration is True

    def test_redundant_grant_returns_conflict(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        test_character.has_heroic_inspiration = True
        session.add(test_character)
        session.commit()

        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/grant",
            headers=dm_headers,
        )

        assert response.status_code == 409

    def test_redundant_revoke_returns_conflict(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/revoke",
            headers=dm_headers,
        )

        assert response.status_code == 409

    def test_redundant_use_returns_conflict(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/use",
            headers=auth_headers,
        )

        assert response.status_code == 409

    def test_archived_party_blocks_heroic_inspiration_mutations(
        self,
        client: TestClient,
        auth_headers: dict,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        test_character.has_heroic_inspiration = True
        test_party.is_active = False
        session.add(test_character)
        session.add(test_party)
        session.commit()

        grant = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/grant",
            headers=dm_headers,
        )
        revoke = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/revoke",
            headers=dm_headers,
        )
        use = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/use",
            headers=auth_headers,
        )

        assert grant.status_code == 400
        assert revoke.status_code == 400
        assert use.status_code == 400

    def test_party_detail_includes_heroic_inspiration(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        test_character.has_heroic_inspiration = True
        session.add(test_character)
        session.commit()

        response = client.get(f"/api/parties/{test_party.code}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["characters"][0]["has_heroic_inspiration"] is True

    def test_successful_action_emits_sse_event(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        test_dm,
        monkeypatch,
    ):
        seen_events: list[tuple[str, dict]] = []

        async def fake_broadcast(party_id: int, event_type: str, data: dict):
            seen_events.append((event_type, data))

        monkeypatch.setattr(event_manager, "broadcast", fake_broadcast)

        response = client.post(
            f"/api/parties/{test_party.code}/heroic-inspiration/{test_character.id}/grant",
            headers=dm_headers,
        )

        assert response.status_code == 200
        assert seen_events == [
            (
                "heroic_inspiration_update",
                {
                    "character_id": test_character.id,
                    "has_heroic_inspiration": True,
                    "action": "granted",
                    "target_user_id": test_character.user_id,
                    "actor_user_id": test_dm.id,
                },
            )
        ]
