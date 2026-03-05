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


class TestSplitToMember:
    """Test joint payments that pay a specific party member (receiver_character_id)."""

    def _create_third_user_and_character(
        self, session: Session, test_party: Party
    ) -> tuple[User, Character, dict]:
        """Helper: create a third user with a character in the party."""
        from app.core.security import hash_password

        user = User(
            username="receiver_player",
            hashed_password=hash_password("password123"),
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        char = Character(
            name="Legolas",
            character_class="Ranger",
            balance_cp=2000,  # 20 GP
            user_id=user.id,
            party_id=test_party.id,
        )
        session.add(char)
        session.commit()
        session.refresh(char)

        token = create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}
        return user, char, headers

    def test_create_split_with_receiver(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """Player creates a split payment that pays a specific party member."""
        _, receiver_char, _ = self._create_third_user_and_character(session, test_party)

        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
                "reason": "Pool money for Legolas' new bow",
                "receiver_character_id": receiver_char.id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"
        assert data["receiver_character_id"] == receiver_char.id
        assert data["receiver_name"] == "Legolas"
        assert data["total_amount_cp"] == 1000

    def test_split_to_member_credits_receiver_on_accept(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """When all participants accept, receiver's balance increases by total amount."""
        _, receiver_char, _ = self._create_third_user_and_character(session, test_party)
        initial_receiver_balance = receiver_char.balance_cp

        # Create split paying the receiver
        create_resp = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
                "receiver_character_id": receiver_char.id,
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        payment_id = create_resp.json()["id"]

        # Both accept
        resp1 = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/accept",
            headers=auth_headers,
        )
        assert resp1.status_code == 200
        assert resp1.json()["status"] == "pending"

        resp2 = client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/accept",
            headers=second_auth_headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "approved"

        # Verify participants lost money
        session.refresh(test_character)
        session.refresh(second_character)
        assert test_character.balance_cp < 10000
        assert second_character.balance_cp < 5000

        # Verify receiver GAINED the total amount
        session.refresh(receiver_char)
        assert receiver_char.balance_cp == initial_receiver_balance + 1000

    def test_dm_creates_split_to_member(
        self,
        client: TestClient,
        dm_headers: dict,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """DM creates a charge where the money goes to a party member."""
        _, receiver_char, _ = self._create_third_user_and_character(session, test_party)

        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments/dm",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 20},
                "reason": "Paying Legolas for services",
                "receiver_character_id": receiver_char.id,
            },
            headers=dm_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["creator_is_dm"] is True
        assert data["receiver_character_id"] == receiver_char.id
        assert data["receiver_name"] == "Legolas"

    def test_receiver_cannot_be_participant(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        """Receiver cannot also be a participant (double role)."""
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 5},
                "receiver_character_id": test_character.id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "receiver cannot also be a participant" in response.json()["detail"].lower()

    def test_receiver_not_in_party_rejected(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """Receiver must belong to the same party."""
        from app.core.security import hash_password

        # Create a character in a DIFFERENT party
        other_dm = User(
            username="other_dm",
            hashed_password=hash_password("password123"),
        )
        session.add(other_dm)
        session.commit()
        session.refresh(other_dm)

        other_party = Party(
            name="Other Party", code="OTHR", dm_id=other_dm.id,
        )
        session.add(other_party)
        session.commit()
        session.refresh(other_party)

        outsider = Character(
            name="Outsider",
            character_class="Bard",
            balance_cp=1000,
            user_id=other_dm.id,
            party_id=other_party.id,
        )
        session.add(outsider)
        session.commit()
        session.refresh(outsider)

        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 5},
                "receiver_character_id": outsider.id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "receiver" in response.json()["detail"].lower()

    def test_inactive_receiver_rejected(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """Inactive (left/kicked) receiver is rejected."""
        _, receiver_char, _ = self._create_third_user_and_character(session, test_party)
        # Deactivate the receiver
        receiver_char.is_active = False
        session.add(receiver_char)
        session.commit()

        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 5},
                "receiver_character_id": receiver_char.id,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "receiver" in response.json()["detail"].lower()

    def test_npc_split_still_works_without_receiver(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """Classic NPC split (no receiver) still removes money from economy."""
        initial_balance_1 = test_character.balance_cp
        initial_balance_2 = second_character.balance_cp

        create_resp = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
                # No receiver_character_id — money disappears
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        data = create_resp.json()
        assert data["receiver_character_id"] is None
        assert data["receiver_name"] is None

        payment_id = data["id"]

        # Both accept
        client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/accept",
            headers=auth_headers,
        )
        client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/accept",
            headers=second_auth_headers,
        )

        # Both lost money, no one gained it
        session.refresh(test_character)
        session.refresh(second_character)
        total_deducted = (initial_balance_1 - test_character.balance_cp) + \
                         (initial_balance_2 - second_character.balance_cp)
        assert total_deducted == 1000

    def test_rejected_split_does_not_credit_receiver(
        self,
        client: TestClient,
        auth_headers: dict,
        second_auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """If a split is rejected, no money moves to or from anyone."""
        _, receiver_char, _ = self._create_third_user_and_character(session, test_party)
        initial_receiver_balance = receiver_char.balance_cp

        create_resp = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
                "receiver_character_id": receiver_char.id,
            },
            headers=auth_headers,
        )
        payment_id = create_resp.json()["id"]

        # Second player rejects
        client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/reject",
            headers=second_auth_headers,
        )

        # No one's balance changed
        session.refresh(test_character)
        session.refresh(second_character)
        session.refresh(receiver_char)
        assert test_character.balance_cp == 10000
        assert second_character.balance_cp == 5000
        assert receiver_char.balance_cp == initial_receiver_balance

    def test_cancelled_split_does_not_credit_receiver(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
        session: Session,
    ):
        """If a split is cancelled, no money moves to or from anyone."""
        _, receiver_char, _ = self._create_third_user_and_character(session, test_party)
        initial_receiver_balance = receiver_char.balance_cp

        create_resp = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 10},
                "receiver_character_id": receiver_char.id,
            },
            headers=auth_headers,
        )
        payment_id = create_resp.json()["id"]

        # Creator cancels
        client.post(
            f"/api/parties/{test_party.code}/joint-payments/{payment_id}/cancel",
            headers=auth_headers,
        )

        # No one's balance changed
        session.refresh(test_character)
        session.refresh(second_character)
        session.refresh(receiver_char)
        assert test_character.balance_cp == 10000
        assert second_character.balance_cp == 5000
        assert receiver_char.balance_cp == initial_receiver_balance

    def test_nonexistent_receiver_rejected(
        self,
        client: TestClient,
        auth_headers: dict,
        test_party: Party,
        test_character: Character,
        second_character: Character,
    ):
        """A non-existent receiver_character_id is rejected."""
        response = client.post(
            f"/api/parties/{test_party.code}/joint-payments",
            json={
                "character_ids": [test_character.id, second_character.id],
                "amount": {"gp": 5},
                "receiver_character_id": 99999,
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "receiver" in response.json()["detail"].lower()

