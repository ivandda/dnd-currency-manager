"""Tests for inventory endpoints and item lifecycle behavior."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.events import event_manager
from app.models.character import Character
from app.models.inventory import InventoryEvent, InventoryEventType, InventoryItem
from app.models.party import Party
from app.models.user import User


def _create_item(
    client: TestClient,
    party_code: str,
    headers: dict,
    *,
    name: str = "Potion",
    amount: int = 1,
    is_public: bool = True,
    owner_character_id: int | None = None,
    description_md: str = "",
):
    payload: dict = {
        "name": name,
        "amount": amount,
        "is_public": is_public,
        "description_md": description_md,
    }
    if owner_character_id is not None:
        payload["owner_character_id"] = owner_character_id

    return client.post(
        f"/api/parties/{party_code}/inventory",
        json=payload,
        headers=headers,
    )


class TestInventoryCreateAndList:
    def test_player_creates_item_for_self(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = _create_item(
            client,
            test_party.code,
            auth_headers,
            name="Rope",
            amount=2,
            is_public=True,
            description_md="**50ft hemp rope**",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Rope"
        assert data["amount"] == 2
        assert data["owner_character_id"] == test_character.id
        assert data["can_edit"] is True

    def test_player_cannot_create_item_for_other_character(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        response = _create_item(
            client,
            test_party.code,
            auth_headers,
            name="Stolen Sword",
            owner_character_id=second_character.id,
        )
        assert response.status_code == 403
        assert "only create items for themselves" in response.json()["detail"]

    def test_dm_can_create_unassigned_or_assigned_items(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        unassigned = _create_item(
            client,
            test_party.code,
            dm_headers,
            name="Prepared Loot",
            owner_character_id=None,
        )
        assert unassigned.status_code == 201
        assert unassigned.json()["owner_character_id"] is None

        assigned = _create_item(
            client,
            test_party.code,
            dm_headers,
            name="DM Gift",
            owner_character_id=test_character.id,
        )
        assert assigned.status_code == 201
        assert assigned.json()["owner_character_id"] == test_character.id

    def test_visibility_filters_items_for_other_players(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        private_item = _create_item(
            client,
            test_party.code,
            auth_headers,
            name="Secret Letter",
            is_public=False,
        )
        public_item = _create_item(
            client,
            test_party.code,
            auth_headers,
            name="Torch",
            is_public=True,
        )
        assert private_item.status_code == 201
        assert public_item.status_code == 201

        mine = client.get(f"/api/parties/{test_party.code}/inventory", headers=auth_headers)
        assert mine.status_code == 200
        mine_names = {item["name"] for item in mine.json()}
        assert "Secret Letter" in mine_names
        assert "Torch" in mine_names

        other = client.get(f"/api/parties/{test_party.code}/inventory", headers=second_auth_headers)
        assert other.status_code == 200
        other_names = {item["name"] for item in other.json()}
        assert "Torch" in other_names
        assert "Secret Letter" not in other_names

    def test_dm_sees_private_items(
        self,
        client: TestClient,
        auth_headers: dict,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        create = _create_item(
            client,
            test_party.code,
            auth_headers,
            name="Hidden Gem",
            is_public=False,
        )
        assert create.status_code == 201

        dm_list = client.get(f"/api/parties/{test_party.code}/inventory", headers=dm_headers)
        assert dm_list.status_code == 200
        names = {item["name"] for item in dm_list.json()}
        assert "Hidden Gem" in names


class TestInventoryUpdateTransferArchiveRestore:
    def test_owner_can_update_item_fields(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Rations", amount=3)
        item_id = create.json()["id"]

        response = client.patch(
            f"/api/parties/{test_party.code}/inventory/{item_id}",
            json={"name": "Travel Rations", "amount": 5, "is_public": False, "description_md": "- dry meat"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Travel Rations"
        assert data["amount"] == 5
        assert data["is_public"] is False

    def test_non_owner_cannot_update_item(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Owner Only")
        item_id = create.json()["id"]

        response = client.patch(
            f"/api/parties/{test_party.code}/inventory/{item_id}",
            json={"amount": 99},
            headers=second_auth_headers,
        )
        assert response.status_code == 403

    def test_owner_can_transfer_item_to_another_player(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Shield")
        item_id = create.json()["id"]

        response = client.post(
            f"/api/parties/{test_party.code}/inventory/{item_id}/transfer",
            json={"owner_character_id": second_character.id},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["owner_character_id"] == second_character.id

    def test_player_cannot_transfer_to_unassigned(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Helmet")
        item_id = create.json()["id"]

        response = client.post(
            f"/api/parties/{test_party.code}/inventory/{item_id}/transfer",
            json={"owner_character_id": None},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_dm_can_transfer_item_to_unassigned(
        self,
        client: TestClient,
        auth_headers: dict,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Ring")
        item_id = create.json()["id"]

        response = client.post(
            f"/api/parties/{test_party.code}/inventory/{item_id}/transfer",
            json={"owner_character_id": None},
            headers=dm_headers,
        )
        assert response.status_code == 200
        assert response.json()["owner_character_id"] is None

    def test_owner_can_archive_and_restore(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Lantern")
        item_id = create.json()["id"]

        archive = client.post(
            f"/api/parties/{test_party.code}/inventory/{item_id}/archive",
            headers=auth_headers,
        )
        assert archive.status_code == 200
        assert archive.json()["is_active"] is False

        restore = client.post(
            f"/api/parties/{test_party.code}/inventory/{item_id}/restore",
            headers=auth_headers,
        )
        assert restore.status_code == 200
        assert restore.json()["is_active"] is True

    def test_cannot_transfer_archived_item(
        self,
        client: TestClient,
        auth_headers: dict,
        second_character: Character,
        test_party: Party,
        test_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Archived Relic")
        item_id = create.json()["id"]

        archive = client.post(
            f"/api/parties/{test_party.code}/inventory/{item_id}/archive",
            headers=auth_headers,
        )
        assert archive.status_code == 200

        transfer = client.post(
            f"/api/parties/{test_party.code}/inventory/{item_id}/transfer",
            json={"owner_character_id": second_character.id},
            headers=auth_headers,
        )
        assert transfer.status_code == 404

    def test_inventory_cap_of_100_active_items(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        test_user: User,
        session: Session,
    ):
        now = datetime.now(timezone.utc)
        for i in range(100):
            session.add(
                InventoryItem(
                    party_id=test_party.id,
                    name=f"Item {i}",
                    description_md="",
                    amount=1,
                    owner_character_id=test_character.id,
                    is_public=True,
                    is_active=True,
                    created_by_user_id=test_user.id,
                    updated_by_user_id=test_user.id,
                    created_at=now,
                    updated_at=now,
                )
            )
        session.commit()

        response = _create_item(client, test_party.code, auth_headers, name="Overflow")
        assert response.status_code == 400
        assert "100 active items" in response.json()["detail"]

    def test_restore_respects_active_item_cap(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        test_user: User,
        session: Session,
    ):
        now = datetime.now(timezone.utc)
        for i in range(100):
            session.add(
                InventoryItem(
                    party_id=test_party.id,
                    name=f"Cap {i}",
                    description_md="",
                    amount=1,
                    owner_character_id=test_character.id,
                    is_public=True,
                    is_active=True,
                    created_by_user_id=test_user.id,
                    updated_by_user_id=test_user.id,
                    created_at=now,
                    updated_at=now,
                )
            )

        archived = InventoryItem(
            party_id=test_party.id,
            name="Archived Token",
            description_md="",
            amount=1,
            owner_character_id=test_character.id,
            is_public=True,
            is_active=False,
            created_by_user_id=test_user.id,
            updated_by_user_id=test_user.id,
            created_at=now,
            updated_at=now,
        )
        session.add(archived)
        session.commit()
        session.refresh(archived)

        response = client.post(
            f"/api/parties/{test_party.code}/inventory/{archived.id}/restore",
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "100 active items" in response.json()["detail"]


class TestInventoryHistoryAndLifecycle:
    def test_private_history_event_is_redacted_for_other_players(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Diary", is_public=False)
        item_id = create.json()["id"]

        update = client.patch(
            f"/api/parties/{test_party.code}/inventory/{item_id}",
            json={"amount": 7},
            headers=auth_headers,
        )
        assert update.status_code == 200

        owner_history = client.get(
            f"/api/parties/{test_party.code}/inventory/history",
            headers=auth_headers,
        )
        assert owner_history.status_code == 200
        owner_events = owner_history.json()["events"]
        assert any(e["redacted"] is False and e["item_name"] == "Diary" for e in owner_events)

        other_history = client.get(
            f"/api/parties/{test_party.code}/inventory/history",
            headers=second_auth_headers,
        )
        assert other_history.status_code == 200
        first = other_history.json()["events"][0]
        assert first["redacted"] is True
        assert first["summary"] == "Private item updated"

    def test_leave_party_moves_items_to_unassigned_stash(
        self,
        client: TestClient,
        auth_headers: dict,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        create = _create_item(client, test_party.code, auth_headers, name="Leaving Item")
        assert create.status_code == 201
        item_id = create.json()["id"]

        leave = client.post(f"/api/parties/{test_party.code}/leave", headers=auth_headers)
        assert leave.status_code == 200

        item = session.get(InventoryItem, item_id)
        assert item is not None
        assert item.owner_character_id is None

        transfer_event = session.exec(
            select(InventoryEvent).where(
                InventoryEvent.item_id == item_id,
                InventoryEvent.event_type == InventoryEventType.ITEM_TRANSFERRED,
            )
        ).first()
        assert transfer_event is not None

        dm_list = client.get(f"/api/parties/{test_party.code}/inventory", headers=dm_headers)
        assert dm_list.status_code == 200
        target = [i for i in dm_list.json() if i["id"] == item_id][0]
        assert target["owner_character_id"] is None

    def test_kick_party_member_moves_items_to_unassigned_stash(
        self,
        client: TestClient,
        dm_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        second_character: Character,
        session: Session,
    ):
        create = _create_item(client, test_party.code, second_auth_headers, name="Kick Item")
        item_id = create.json()["id"]

        kick = client.post(
            f"/api/parties/{test_party.code}/kick",
            json={"character_id": second_character.id},
            headers=dm_headers,
        )
        assert kick.status_code == 200

        item = session.get(InventoryItem, item_id)
        assert item is not None
        assert item.owner_character_id is None

    def test_archived_party_blocks_inventory_mutations(
        self,
        client: TestClient,
        auth_headers: dict,
        dm_headers: dict,
        test_party: Party,
    ):
        archive_party = client.patch(f"/api/parties/{test_party.code}/archive", headers=dm_headers)
        assert archive_party.status_code == 200

        create = _create_item(client, test_party.code, auth_headers, name="Blocked")
        assert create.status_code == 400
        assert "archived" in create.json()["detail"].lower()

    def test_inventory_mutations_emit_inventory_update_event(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        monkeypatch,
    ):
        seen_events: list[str] = []

        async def fake_broadcast(party_id: int, event_type: str, data: dict):
            seen_events.append(event_type)

        monkeypatch.setattr(event_manager, "broadcast", fake_broadcast)

        create = _create_item(client, test_party.code, auth_headers, name="SSE Item")
        assert create.status_code == 201
        assert "inventory_update" in seen_events
