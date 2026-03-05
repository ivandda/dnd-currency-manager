"""Tests for joint payment endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models.character import Character
from app.models.party import Party
from app.models.user import User
from app.core.security import create_access_token


class TestCreateJointPayment:
    """Test creating joint payment requests."""

    def test_player_creates_joint_payment(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
                "reason": "Buying a horse",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["total_amount_cp"] == 1000
        assert data["creator_is_dm"] is False
        assert len(data["participants"]) == 2
        # Total of shares should equal total amount
        total_shares = sum(p["share_cp"] for p in data["participants"])
        assert total_shares == 1000

    def test_dm_creates_charge(
        self,
        client: TestClient,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments/dm",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 50},
                "reason": "Tavern bill",
            },
            headers=dm_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["creator_is_dm"] is True
        assert data["status"] == "pending"

    def test_insufficient_funds_on_create(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 500},  # 50000 CP > available
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "insufficient funds" in response.json()["detail"].lower()


class TestAcceptJointPayment:
    """Test accepting joint payment requests."""

    def test_accept_and_execute(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        # Create joint payment
        create_response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
                "reason": "Shared purchase",
            },
            headers=auth_headers,
        )
        assert create_response.status_code == 201
        payment_id = create_response.json()["id"]

        # First player accepts
        accept1 = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/accept",
            headers=auth_headers,
        )
        assert accept1.status_code == 200
        assert accept1.json()["status"] == "pending"  # Still waiting for player 2

        # Second player accepts
        accept2 = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/accept",
            headers=second_auth_headers,
        )
        assert accept2.status_code == 200
        assert accept2.json()["status"] == "approved"  # All accepted!

        # Check balances were deducted
        session.refresh(test_character)
        session.refresh(second_character)
        assert test_character.balance_cp < 10000
        assert second_character.balance_cp < 5000

    def test_non_participant_cannot_accept(
        self,
        client: TestClient,
        auth_headers: dict,
        dm_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        # DM creates a charge for both players
        create_response = client.post(
            f"/api/parties/{test_party.code}/joint-payments/dm",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
            },
            headers=dm_headers,
        )
        payment_id = create_response.json()["id"]

        # Create a third user who is not a participant
        from app.core.security import hash_password
        third_user = User(
            username="outsider",
            hashed_password=hash_password("password123"),
        )
        session.add(third_user)
        session.commit()
        session.refresh(third_user)

        # Give the outsider a character in the party
        outsider_char = Character(
            name="Outsider",
            character_class="Bard",
            balance_cp=5000,
            user_id=third_user.id,
            party_id=test_party.id,
        )
        session.add(outsider_char)
        session.commit()

        third_token = create_access_token(third_user.id)
        third_headers = {"Authorization": f"Bearer {third_token}"}

        # Outsider tries to accept
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/accept",
            headers=third_headers,
        )
        assert response.status_code == 403


class TestRejectJointPayment:
    """Test rejecting joint payment requests."""

    def test_reject_payment(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        # Create joint payment
        create_response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
            },
            headers=auth_headers,
        )
        payment_id = create_response.json()["id"]

        # Second player rejects
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/reject",
            headers=second_auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"

        # Verify balances unchanged
        session.refresh(test_character)
        session.refresh(second_character)
        assert test_character.balance_cp == 10000
        assert second_character.balance_cp == 5000


class TestCancelJointPayment:
    """Test cancelling joint payment requests."""

    def test_creator_cancels(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        # Create joint payment
        create_response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
            },
            headers=auth_headers,
        )
        payment_id = create_response.json()["id"]

        # Creator cancels
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/cancel",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_non_creator_cannot_cancel(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        # Create joint payment
        create_response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
            },
            headers=auth_headers,
        )
        payment_id = create_response.json()["id"]

        # Other player tries to cancel
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/cancel",
            headers=second_auth_headers,
        )
        assert response.status_code == 403


class TestListJointPayments:
    """Test listing joint payments."""

    def test_list_payments(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        # Create two payments
        for i in range(2):
            client.post(
                f"/api/parties/{test_party.code}/joint-payments",
                json={
                    "character_ids": [test_character.id, second_character.id],
                    "amount": {"gp": 5},
                    "reason": f"Payment {i}",
                },
                headers=auth_headers,
            )

        response = client.get(
            f"/api/parties/{test_party.code}/joint-payments",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
