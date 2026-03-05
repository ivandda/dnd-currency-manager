![D&D Currency Manager](docs/imgs/coins_image.png)

# ⚔️ D&D Currency Manager — LAN Party

Real-time currency management for Dungeons & Dragons parties, designed to run on a local network (LAN).

> **DM creates a party → Players join with a code → Everyone manages coins in real time.**

## Features

- 💱 **P2P Transfers** — Players send coins to each other
- 💰 **DM Loot Distribution** — Split treasure evenly among selected players
- ⚡ **DM God Mode** — Add or deduct funds from any character
- 🤝 **Joint Payments** — Split costs among party members
- 🪙 **Multi-currency support** — Platinum, Gold, Electrum, Silver, Copper (configurable per party)
- 📡 **Real-time updates** — SSE keeps all clients in sync

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- Git

### 1. Clone & configure

```bash
git clone https://github.com/ivandda/dnd-currency-manager-lan
cd dnd-currency-manager-lan
cp .env.example .env
```

> Edit `.env` if you want to change the database credentials or secret key.

### 2. Start the app

```bash
docker compose up -d --build
```

This starts 3 services:

| Service      | URL                          | Description            |
|-------------|------------------------------|------------------------|
| **Frontend** | http://localhost:3000         | Next.js UI             |
| **Backend**  | http://localhost:8000         | FastAPI API            |
| **API Docs** | http://localhost:8000/docs    | Swagger UI             |
| **Database** | localhost:5432               | PostgreSQL (internal)  |

### 3. Use the app

1. Open **http://localhost:3000**
2. Share the **LAN URL** with other players
3. **Create an account** (click "Create Account" tab)
4. **Create a party** — you become the DM, get a 4-character party code
5. Share the code with your players
6. Players **register** → **join** with the code + character name & class
7. Start managing currency! 🎲

### 4. Share on LAN

The app auto-detects the host's IP — players just need the URL. Find your LAN IP:

```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'

# Windows
ipconfig | findstr "IPv4"
```

Then share this URL with your players:

```
http://<YOUR_LAN_IP>:3000
```

For example: `http://192.168.1.42:3000`

> The frontend auto-detects the backend URL from the browser's hostname, so players don't need to configure anything — they just open the link and play.

## Development

### Run backend tests

```bash
cd backend
uv run pytest tests/ -v
```

### Run backend locally (without Docker)

```bash
cd backend
# Make sure PostgreSQL is running on localhost:5432
# Update DATABASE_URL in .env to point to localhost instead of 'db'
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run frontend locally (without Docker)

```bash
cd frontend
pnpm install
pnpm dev
```

### View logs

```bash
docker compose logs -f           # All services
docker compose logs -f backend   # Backend only
docker compose logs -f frontend  # Frontend only
```

### Restart a service

```bash
docker compose restart backend
```

### Full rebuild (if dependencies changed)

```bash
docker compose down
docker compose up -d --build
```

### Reset everything (database included)

```bash
docker compose down -v
docker compose up -d --build
```

> ⚠️ `down -v` deletes the database volume. All data will be lost.

---

## Data Persistence

- **Database** — PostgreSQL data is stored in a Docker named volume (`postgres_data`). It survives container restarts and rebuilds. Only `docker compose down -v` will delete it.
- **Backend venv** — Stored in a named volume (`backend_venv`). Dependencies are re-synced on every container start.
- **Frontend node_modules** — Stored in a named volume (`frontend_node_modules`).

---

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Frontend  | Next.js 16, React 19, Tailwind v4, shadcn/ui |
| Backend   | FastAPI, SQLModel, Pydantic v2      |
| Database  | PostgreSQL 16                       |
| Auth      | JWT (access + refresh via httpOnly cookie) |
| Real-time | Server-Sent Events (SSE)            |
| DevOps    | Docker Compose, uv, pnpm           |

---
