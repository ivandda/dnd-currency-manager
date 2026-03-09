# Product Requirements Document (PRD): D&D Currency Manager

## 1. Product Summary

A Full-Stack web application designed to run on a Local Area Network (LAN) that allows Dungeons & Dragons players and the Dungeon Master (DM) to manage in-game currency digitally, in real-time, and without friction.
**Core Principle:** KISS (Keep It Simple, Stupid).

## 2. Tech Stack & Architecture

* **Language Requirement:** All source code (variables, comments, structure) and the User Interface (UI) must be entirely in **English**.
* **Frontend:** Next.js (React) with TypeScript.
* **Styling:** TailwindCSS + shadcn/ui component library.
* **Backend:** Python with FastAPI (chosen specifically to handle Server-Sent Events natively and simply).
* **Database:** PostgreSQL.
* **ORM & Migrations:** SQLModel (Pydantic + SQLAlchemy) and Alembic.
* **Dependency Management:** Use `uv` for local environment management, syncing and exporting to a standard `requirements.txt` file for deployment.
* **Infrastructure:** The entire project must be containerized using Docker (and Docker Compose) to allow one-click deployment on the LAN host machine.

## 3. Entities & Roles

* **User:** Physical account (requires registration with username and password). A User can be a DM in one party and a Player in a different party, but cannot hold both roles within the same party. A User can DM multiple parties simultaneously.
* **Character:** Belongs to a User. A user can have multiple characters across different campaigns (e.g., two characters named "Gimli" in different parties if desired), but a single character instance belongs to **only one** Party. Characters have a **name** and a **class** (e.g., Warrior, Mage, Rogue). Characters cannot be deleted, only archived (left the party).
* **Dungeon Master (DM):** A role with elevated privileges ("God Mode") within a Party. The DM does not have a personal wallet; instead, they act as the bank/world.
* **Party:** A grouping of characters and one DM. Has a display **name** and a short alphanumeric join **code**. Parties can be archived by the DM (no new transactions allowed).

## 4. Authentication & Session Management

* **Strategy:** JWT-based authentication.
  * **Access Token:** Short-lived, stored in memory on the frontend.
  * **Refresh Token:** Long-lived, stored in an `httpOnly` secure cookie for session persistence across browser restarts.
* **Password Hashing:** bcrypt.
* **Registration:** Open — any user can create an account, then join a party using a code.
* **Token Refresh:** The frontend silently refreshes the access token using the refresh token cookie before expiration.

## 5. Core Features

### 5.1. Party Management

* The DM creates a Party (providing a **name**), and the system generates a short alphanumeric code (e.g., `A4F2`).
* Players enter this code on a "Join Party" screen, provide a **character name** and **class**, and their character is linked to the party.
* The DM can **kick** a player from the party.
* A player can **leave** a party voluntarily.
* The DM can **archive** a party (disabling all new transactions).

### 5.2. Currency Engine

* **Base Storage:** All mathematical logic and database storage are handled in the lowest denomination coin (Copper / CP).
* **Standard Exchange Rates:** Hardcoded to standard D&D rules (1 Platinum = 10 Gold, 1 Gold = 10 Silver, 1 Silver = 10 Copper, 1 Electrum = 5 Silver).
* **DM Configuration:** The DM can enable or disable specific coins for their campaign (Default: Gold, Silver, and Copper enabled; Electrum and Platinum disabled).
* **Display & UI:**
  * The UI automatically converts the total copper balance to the cleanest possible format based on the enabled coins (e.g., `1 Gold, 5 Silver, 2 Copper`).
  * The user has a UI toggle to view their entire balance translated into a single specific currency if desired (e.g., "View all in Copper").

### 5.3. Real-Time Transactions & DM Powers

* **Server-Sent Events (SSE):** The backend emits update events to connected clients so screens refresh instantly without reloading, keeping network load light on the LAN.
  * **Connection:** One SSE connection per authenticated user, scoped to their active party.
  * **Event Types:** `balance_update`, `transaction_new`, `joint_payment_update`, `party_update`, `inventory_update`.
  * **Reconnection:** Auto-reconnect with exponential backoff on the frontend.
* **Network Auto-detection:** App includes a backend endpoint (`/api/network/lan-url`) and start script (`start.sh`) to automatically detect the host's actual LAN IP for easy sharing, bypassing Docker networking limitations.
* **DM Dashboard:** The DM has a real-time overview of every character's wallet and balance in the Party.
* **Per-User Coin Preferences:** Coin visibility (gold/electrum/platinum) is configured per user per party, not globally by DM.
* **P2P Transfers:** Characters can send money to each other.
* **Balance Privacy:** Each player can choose whether their wallet balance is visible to other players in that party. DM always sees all balances.
* **NPC Spend:** Characters can spend money on NPC purchases (shops, tolls, etc.). Money leaves the economy.
* **Self-Add Funds:** Players can add money to their own wallet (found loot, sold items) without DM approval. All self-adds are recorded in the immutable transaction history.
* **Looting (DM to Players):** The DM can transfer funds to one or multiple players simultaneously. These funds are generated infinitely (they are not deducted from a DM wallet).
* **DM God Mode:** The DM can directly add or subtract money from a player's wallet without requiring permission.
* **Immutability:** Every movement generates an immutable record in the transaction history. An optional reason/note can be attached to any transfer. No one, not even the DM, can alter the transaction history.

### 5.4. Joint Payments System

There are two distinct joint payment flows:

1. **Player-Initiated Split:** A character initiates a request: "Let's pool money to buy X." All selected players pay their share.
2. **DM-Initiated Charge:** The DM charges the party: "The tavern charges you 50gp." Money is deducted from each selected player equally.

**Common rules:**
* **Recipient:** Joint payment money is either removed from the economy (NPC purchase/world charge) OR can be directed to a specific **Party Member** (e.g., "Pay the Rogue for lockpicks"). If a member is the receiver, they get credited the full amount when the split is approved.
* **Acceptance Rule:** Requires 100% acceptance from all involved parties to be executed.
* **Request States:**
  * *Pending:* Waiting for responses.
  * *Cancelled:* The creator of the request clicks the "Cancel Request" button to drop it before everyone accepts.
  * *Rejected / Blocked:* If anyone clicks "Reject" or if the system detects that someone has insufficient funds (balances cannot go into the negative).
  * *Approved:* Everyone accepts, and the money is deducted.
* **Remainder Handling:** If splitting a payment generates a copper remainder that cannot be divided equally, that indivisible coin is automatically assigned to a random player among those involved.

### 5.5. Inventory Manager

The app includes a simple, party-scoped item inventory system for players and DMs.

**Data model (MVP):**
* `name` (required)
* `description_md` (Markdown description, rendered safely in frontend)
* `amount` (non-negative integer)
* `owner_character_id` (single owner, nullable for DM stash)
* `is_public` (privacy flag)
* `created_at`, `updated_at`, `created_by_user_id`, `updated_by_user_id`
* `is_active` (soft delete/archive)

**Permissions and behavior:**
* Players can create items for themselves only.
* DM can create items for any active player or unassigned stash.
* Owner can edit their own items; DM can edit any item.
* Any player can transfer ownership of their own items to any active player.
* DM can transfer any item to any active player or unassigned stash.
* DM always sees all items.
* Non-owner players can only see items marked public.
* Party inventory is capped at **100 active items** (no pagination).
* Party archived state blocks all inventory writes.
* If owner leaves or is kicked, their items are reassigned automatically to unassigned stash.

**History integration:**
* Inventory lifecycle events are immutable and appear in the same History tab as currency events.
* Event types: `item_created`, `item_updated`, `item_amount_changed`, `item_visibility_changed`, `item_transferred`, `item_deleted`, `item_restored`.
* History supports filters: All | Currency | Inventory.
* Private item history is redacted for unauthorized viewers (`"Private item updated"`), while DM and authorized owners see full detail.

**Lifecycle coverage:**
1. Create (self/DM/unassigned)
2. View (privacy-aware)
3. Update (name/description/amount/visibility)
4. Transfer ownership
5. Archive (soft delete)
6. Restore
7. Track every transition in immutable history + real-time SSE updates

## 6. Pages & Navigation

The application is **mobile-responsive** (players will use phones on the LAN).

| Page | Path | Description |
|------|------|-------------|
| Login | `/login` | Username + password |
| Register | `/register` | Create account |
| Dashboard | `/` | List of user's characters + parties |
| Create Party | `/party/create` | DM creates a new party (name only) |
| Join Party | `/party/join` | Enter party code + character name & class |
| Party View (Player) | `/party/[code]` | Character wallet, transfer, inventory, splits, history |
| Party View (DM) | `/party/[code]/dm` | DM dashboard: wallets, loot, inventory control, god mode |
| Transaction History | `/party/[code]/history` | Immutable log of all transactions |

## 7. UI & Design Direction

* **Theme:** D&D Beyond-inspired styles with a persistent theme toggle (🌙 Dark / ☀️ Light). 
  * **Dark:** Deep charcoal/midnight blue, red accent, clean and professional.
  * **Light (Parchment):** Warm cream/parchment backgrounds with rich medieval card styles and distinct contrast.
* **Typography:** Inter (sans-serif) for body text — optimized for mobile readability. Cinzel (serif) for headings — medieval fantasy feel.
* **Components:** TailwindCSS + shadcn/ui, customized to fit the fantasy theme. Native CSS variables used for theme support.
* **Responsiveness & Mobile-First:** Players will primarily use phones. Swipeable tabs, ≥44px touch targets. Includes native-feeling features like **Pull-to-Refresh**.
* **Layout:** 5-tab party view: Party (members, settings) | Treasury (unified transfer card) | Inventory | Splits (joint payments) | History. 
  * **Bottom Bar:** Mobile-only fixed bottom bar showing character's active coin balance (or DM Badge).
  * **Interactive Coins:** Tapping coins auto-converts the display to that specific denomination on the fly.
  * **Animations:** Smooth number-counting component (`requestAnimationFrame`) for balance changes to highlight additions/deductions naturally.
  * **Empty States:** Themed inline SVGs (swords, chests, scrolls) for empty tabs to prevent blank-screen syndrome.
* **Transfer Card:** Unified card with 3 modes: Send to member, NPC/Shop purchase, Add to self. Eliminates confusion of multiple separate sections.
* **Inventory UX:** Search by name/description, owner-aware sections (My Items/Public Party Items for players; All/Unassigned for DM), and archive/restore actions.
* **Markdown Rendering:** Item descriptions render as sanitized Markdown (no unsafe raw HTML execution).

## 8. API Design

* **Style:** RESTful with clear resource-based URLs.
* **Base Path:** `/api`
* **Key Endpoint Groups:**
  * `/api/auth` — Register, login, refresh token, logout
  * `/api/users` — User profile
  * `/api/parties` — CRUD for parties, join/leave
  * `/api/parties/{code}/characters` — Characters within a party
  * `/api/parties/{code}/transactions` — Transaction history
  * `/api/parties/{code}/transfers` — Create transfers (P2P, DM loot, DM god mode)
  * `/api/parties/{code}/joint-payments` — Joint payment CRUD and accept/reject
  * `/api/parties/{code}/inventory` — Inventory CRUD + ownership transfer + archive/restore
  * `/api/parties/{code}/inventory/history` — Immutable inventory history with privacy-aware redaction
  * `/api/sse` — SSE stream endpoint
* **Error Handling:** Consistent JSON error responses with `{ "detail": "message" }` format.
* **Validation:** Pydantic schemas for all request/response bodies.

## 9. Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dnd_currency

# Auth
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# App
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

## 10. Docker Architecture

* **Services (docker-compose.yaml):**
  * `frontend` — Next.js app
  * `backend` — FastAPI app
  * `db` — PostgreSQL
* **Networking:** All services on the same Docker network, frontend and backend exposed on the LAN.
* **Volumes:** PostgreSQL data persistence via named volume.
* **One-click start:** `docker compose up --build` to launch the entire stack.

## 11. Quality Assurance (QA) & Gitflow

* **Gitflow:** Simplified model. `main` branch for production (what gets packed into Docker), and development via `feature/feature-name` branches with Pull Requests to `main`.
* **Backend Testing:** Comprehensive automated tests using `pytest` focusing on:
  * Currency conversion logic.
  * Balance mathematics (addition, subtraction, division with random remainders).
  * Insufficient funds validation.
  * Inventory permissions/privacy matrix (DM vs owner vs other players).
  * Item lifecycle (create/update/transfer/archive/restore).
  * Archived party write-blocks and item-cap enforcement (100 active items).
  * Inventory history redaction behavior and SSE inventory event emission.
* **Frontend Testing:** Unit tests to ensure UI components correctly translate and render currencies visually.

---

# Database Schema

All models use SQLModel (Pydantic + SQLAlchemy) with Alembic for migrations.

```python
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
from enum import Enum


class TransactionType(str, Enum):
    TRANSFER = "transfer"           # P2P character-to-character
    DM_GRANT = "dm_grant"           # DM gives money (loot)
    DM_DEDUCT = "dm_deduct"         # DM removes money (god mode)
    JOINT_PAYMENT = "joint_payment" # Joint payment deduction
    SPEND = "spend"                 # Player spends on NPC/shop
    SELF_ADD = "self_add"           # Player adds money to own wallet


class JointPaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    characters: List["Character"] = Relationship(back_populates="user")
    parties_as_dm: List["Party"] = Relationship(back_populates="dm")


class Party(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    code: str = Field(unique=True, index=True)  # e.g. "A4F2"
    dm_id: int = Field(foreign_key="user.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Coin configuration (Copper and Silver always enabled by default)
    use_gold: bool = Field(default=True)
    use_electrum: bool = Field(default=False)
    use_platinum: bool = Field(default=False)

    # Relationships
    dm: User = Relationship(back_populates="parties_as_dm")
    characters: List["Character"] = Relationship(back_populates="party")


class Character(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    character_class: str  # e.g. "Warrior", "Mage", "Rogue"
    balance_cp: int = Field(default=0)  # All stored in copper
    is_active: bool = Field(default=True)  # False = left the party / archived
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user_id: int = Field(foreign_key="user.id")
    party_id: int = Field(foreign_key="party.id")

    # Relationships
    user: User = Relationship(back_populates="characters")
    party: Party = Relationship(back_populates="characters")


class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_type: TransactionType
    amount_cp: int  # Always positive; type determines direction
    reason: Optional[str] = Field(default=None)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    party_id: int = Field(foreign_key="party.id")
    # Null sender = DM-generated funds (dm_grant)
    sender_id: Optional[int] = Field(default=None, foreign_key="character.id")
    # Null receiver = money removed from economy (joint_payment cost)
    receiver_id: Optional[int] = Field(default=None, foreign_key="character.id")
    # Link to joint payment if applicable
    joint_payment_id: Optional[int] = Field(default=None, foreign_key="jointpayment.id")


class JointPayment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Creator can be a character_id or null (if DM-initiated)
    creator_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    creator_is_dm: bool = Field(default=False)
    party_id: int = Field(foreign_key="party.id")
    # Optional receiver (if split is explicitly paying a party member)
    receiver_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    total_amount_cp: int
    reason: Optional[str] = Field(default=None)
    status: JointPaymentStatus = Field(default=JointPaymentStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    participants: List["PaymentParticipant"] = Relationship(back_populates="joint_payment")


class PaymentParticipant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    joint_payment_id: int = Field(foreign_key="jointpayment.id")
    character_id: int = Field(foreign_key="character.id")
    share_cp: int  # Pre-calculated share for this participant
    has_accepted: bool = Field(default=False)

    joint_payment: JointPayment = Relationship(back_populates="participants")


class InventoryEventType(str, Enum):
    ITEM_CREATED = "item_created"
    ITEM_UPDATED = "item_updated"
    ITEM_AMOUNT_CHANGED = "item_amount_changed"
    ITEM_VISIBILITY_CHANGED = "item_visibility_changed"
    ITEM_TRANSFERRED = "item_transferred"
    ITEM_DELETED = "item_deleted"
    ITEM_RESTORED = "item_restored"


class InventoryItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    party_id: int = Field(foreign_key="party.id", index=True)
    name: str = Field(min_length=1, max_length=120)
    description_md: str = Field(default="", max_length=10000)
    amount: int = Field(default=1, ge=0)
    owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    is_public: bool = Field(default=True)
    is_active: bool = Field(default=True)
    created_by_user_id: int = Field(foreign_key="user.id")
    updated_by_user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InventoryEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    party_id: int = Field(foreign_key="party.id", index=True)
    item_id: int = Field(foreign_key="inventoryitem.id", index=True)
    event_type: InventoryEventType
    actor_user_id: int = Field(foreign_key="user.id")
    item_name_snapshot: Optional[str] = Field(default=None, max_length=120)
    owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    old_owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    new_owner_character_id: Optional[int] = Field(default=None, foreign_key="character.id")
    old_amount: Optional[int] = None
    new_amount: Optional[int] = None
    old_is_public: Optional[bool] = None
    new_is_public: Optional[bool] = None
    is_public_snapshot: bool = Field(default=True)
    note: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

---

# Coding Standards

- Always use `uv` for dependency management
- Always use FastAPI for backend
- Always use Next.js with TypeScript for frontend
- Always use TailwindCSS + shadcn/ui for styling and components
- Always use SQLModel for data modeling
- Always use Alembic for migrations
- Always use `pytest` for testing
- Always use Docker and Docker Compose for containerization
- Always use Server-Sent Events (SSE) for real-time updates
- Always use LAN for deployment
- Always use English for all source code (variables, comments, structure) and UI
- Always use KISS (Keep It Simple, Stupid) principle
- Always use Pydantic for data validation
- Always maintain the SSOT (Single Source of Truth) file updated
- Always maintain the `.env.example` file updated
- Mobile-responsive design is mandatory

---

# Gitflow

Simplified gitflow: `main` branch for production, development via `feature/feature-name` branches with Pull Requests to `main`.
