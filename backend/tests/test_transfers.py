"""Tests for transfer endpoints (P2P, DM loot, DM god mode)."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.character import Character
from app.models.party import Party
from app.models.user import User


class TestP2PTransfer:
    """Test player-to-player transfers."""

    def test_transfer_success(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/p2p",
            json={
                "receiver_id": second_character.id,
                "amount": {"gp": 10},
                "reason": "Buying a sword",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount_cp"] == 1000  # 10 GP = 1000 CP
        assert data["transaction_type"] == "transfer"
        assert data["sender_name"] == "Gandalf"
        assert data["receiver_name"] == "Aragorn"

        # Verify balances
        session.refresh(test_character)
        session.refresh(second_character)
        assert test_character.balance_cp == 9000  # 10000 - 1000
        assert second_character.balance_cp == 6000  # 5000 + 1000

    def test_transfer_insufficient_funds(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/p2p",
            json={
                "receiver_id": second_character.id,
                "amount": {"gp": 200},  # 20000 CP > 10000 CP balance
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Insufficient funds" in response.json()["detail"]

    def test_transfer_to_self(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/p2p",
            json={
                "receiver_id": test_character.id,
                "amount": {"gp": 1},
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "yourself" in response.json()["detail"]

    def test_transfer_zero_amount(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/p2p",
            json={
                "receiver_id": second_character.id,
                "amount": {"gp": 0},
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_transfer_mixed_coins(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/p2p",
            json={
                "receiver_id": second_character.id,
                "amount": {"gp": 1, "sp": 5, "cp": 3},
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["amount_cp"] == 153  # 100 + 50 + 3


class TestDMLoot:
    """Test DM granting money to players."""

    def test_loot_single_player(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/loot",
            json={
                "character_ids": [test_character.id],
                "amount": {"gp": 50},
                "reason": "Dragon hoard",
            },
            headers=dm_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1
        assert data[0]["transaction_type"] == "dm_grant"
        assert data[0]["amount_cp"] == 5000
        assert data[0]["sender_id"] is None  # DM = no sender

        session.refresh(test_character)
        assert test_character.balance_cp == 15000  # 10000 + 5000

    def test_loot_multiple_players(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/loot",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 25},
            },
            headers=dm_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 2

        session.refresh(test_character)
        session.refresh(second_character)
        assert test_character.balance_cp == 12500  # +2500 each
        assert second_character.balance_cp == 7500

    def test_loot_non_dm_forbidden(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/loot",
            json={
                "character_ids": [test_character.id],
                "amount": {"gp": 50},
            },
            headers=auth_headers,
        )
        assert response.status_code == 403


class TestDMGodMode:
    """Test DM god mode (add/subtract)."""

    def test_god_mode_add(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/god-mode",
            json={
                "character_id": test_character.id,
                "amount": {"gp": 10},
                "is_deduction": False,
                "reason": "Reward for bravery",
            },
            headers=dm_headers,
        )
        assert response.status_code == 201

        session.refresh(test_character)
        assert test_character.balance_cp == 11000

    def test_god_mode_deduct(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        session: Session,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/god-mode",
            json={
                "character_id": test_character.id,
                "amount": {"gp": 5},
                "is_deduction": True,
                "reason": "Taxes",
            },
            headers=dm_headers,
        )
        assert response.status_code == 201
        assert response.json()["transaction_type"] == "dm_deduct"

        session.refresh(test_character)
        assert test_character.balance_cp == 9500

    def test_god_mode_deduct_exceeds_balance(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/transfers/god-mode",
            json={
                "character_id": test_character.id,
                "amount": {"gp": 200},
                "is_deduction": True,
            },
            headers=dm_headers,
        )
        assert response.status_code == 400
        assert "Cannot deduct" in response.json()["detail"]
