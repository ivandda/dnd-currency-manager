# Product Requirements Document (PRD): D&D Currency Manager

## 1. Product Summary

A Full-Stack web application designed to run on a Local Area Network (LAN) that allows Dungeons & Dragons players and the Dungeon Master (DM) to manage in-game currency digitally, in real-time, and without friction.
**Core Principle:** KISS (Keep It Simple, Stupid).

## 2. Tech Stack & Architecture

* **Language Requirement:** All source code (variables, comments, structure) and the User Interface (UI) must be entirely in **English**.
* **Frontend:** Next.js (React).
* **Backend:** Python with FastAPI (chosen specifically to handle Server-Sent Events natively and simply).
* **Database:** PostgreSQL.
* **ORM & Migrations:** SQLModel (Pydantic + SQLAlchemy) and Alembic.
* **Dependency Management:** Use `uv` for local environment management, syncing and exporting to a standard `requirements.txt` file for deployment.
* **Infrastructure:** The entire project must be containerized using Docker (and Docker Compose) to allow one-click deployment on the LAN host machine.

## 3. Entities & Roles

* **User:** Physical account (requires registration with username and password). Maintains an active browser session using a token.
* **Character:** Belongs to a User. A user can have multiple characters across different campaigns (e.g., two characters named "Gimli" in different parties if desired), but a single character instance belongs to **only one** Party.
* **Dungeon Master (DM):** A role with elevated privileges ("God Mode") within a Party. The DM does not have a personal wallet; instead, they act as the bank/world.
* **Party:** A grouping of characters and one DM.

## 4. Core Features

### 4.1. Party Management

* The DM creates a Party, and the system generates a short alphanumeric code (e.g., `A4F2`).
* Players enter this code on a "Join Party" screen to link their character to the table.

### 4.2. Currency Engine

* **Base Storage:** All mathematical logic and database storage are handled in the lowest denomination coin (Copper / CP).
* **Standard Exchange Rates:** Hardcoded to standard D&D rules (1 Platinum = 10 Gold, 1 Gold = 10 Silver, 1 Silver = 10 Copper, 1 Electrum = 5 Silver).
* **DM Configuration:** The DM can enable or disable specific coins for their campaign (Default: Gold, Silver, and Copper enabled; Electrum and Platinum disabled).
* **Display & UI:** * The UI automatically converts the total copper balance to the cleanest possible format based on the enabled coins (e.g., `1 Gold, 5 Silver, 2 Copper`).
* The user has a UI toggle to view their entire balance translated into a single specific currency if desired (e.g., "View all in Copper").



### 4.3. Real-Time Transactions & DM Powers

* **Server-Sent Events (SSE):** The backend emits update events to connected clients so screens refresh instantly without reloading, keeping network load light on the LAN.
* **DM Dashboard:** The DM has a real-time overview of every character's wallet and balance in the Party.
* **P2P Transfers:** Characters can send money to each other.
* **Looting (DM to Players):** The DM can transfer funds to one or multiple players simultaneously. These funds are generated infinitely (they are not deducted from a DM wallet).
* **DM God Mode:** The DM can directly add or subtract money from a player's wallet without requiring permission.
* **Immutability:** Every movement generates an immutable record in the transaction history. An optional reason/note can be attached to any transfer. No one, not even the DM, can alter the transaction history.

### 4.4. Joint Payments System

* A character or the DM can initiate a "Joint Payment Request" for a specific amount to be split among selected participants.
* **Acceptance Rule:** Requires 100% acceptance from all involved parties to be executed.
* **Request States:**
* *Pending:* Waiting for responses.
* *Cancelled:* The creator of the request clicks the "Cancel Request" button to drop it before everyone accepts.
* *Rejected / Blocked:* If anyone clicks "Reject" or if the system detects that someone has insufficient funds (balances cannot go into the negative).
* *Approved:* Everyone accepts, and the money is deducted.


* **Remainder Handling:** If splitting a payment or loot generates a copper remainder that cannot be divided equally, that indivisible coin is automatically assigned to a random player among those involved.

## 5. Quality Assurance (QA) & Gitflow

* **Gitflow:** Simplified model. `main` branch for production (what gets packed into Docker), and development via `feature/feature-name` branches with Pull Requests to `main`.
* **Backend Testing:** Comprehensive automated tests using `pytest` focusing on:
* Currency conversion logic.
* Balance mathematics (addition, subtraction, division with random remainders).
* Insufficient funds validation.


* **Frontend Testing:** Unit tests to ensure UI components correctly translate and render currencies visually.

---


# Possible data model

(Always using almebic and SQLModel)

---

# Coding Standards

- Always use uv for dependency management
- Always use FastAPI for backend
- Always use Next.js for frontend
- Always use SQLModel for data modeling
- Always use Alembic for migrations
- Always use pytest for testing
- Always use Docker for containerization
- Always use Server-Sent Events (SSE) for real-time updates
- Always use LAN for deployment
- Always use English for all source code (variables, comments, structure) and UI
- Always use KISS (Keep It Simple, Stupid) principle
- Always use pydantic for data validation
- Always mantain the SSOT (Single Source of Truth) file updated
- Always use Docker Compose for containerization
- Always mantain the .env.example file updated

---

# Gitflow

(Always using simplified gitflow with main and feature branches)