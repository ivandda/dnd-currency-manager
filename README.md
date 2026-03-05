# ⚔️ D&D Currency Manager — LAN Party Edition

Real-time currency management for Dungeons & Dragons parties, designed to run on a local network.

> **DM creates a party → Players join with a code → Everyone manages coins in real time.**

## Features

- 🪙 **Multi-currency support** — Platinum, Gold, Electrum, Silver, Copper (configurable per party)
- 💱 **P2P Transfers** — Players send coins to each other
- 💰 **DM Loot Distribution** — Split treasure evenly among selected players
- ⚡ **DM God Mode** — Add or deduct funds from any character
- 🤝 **Joint Payments** — Split costs among party members (requires acceptance)
- 📡 **Real-time updates** — SSE keeps all clients in sync
- 🏰 **Medieval fantasy UI** — Dark themed with gold accents

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- Git

### 1. Clone & configure

```bash
git clone <repo-url>
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
2. **Create an account** (click "Create Account" tab)
3. **Create a party** — you become the DM, get a 4-character party code
4. Share the code with your players on the same network
5. Players **register** → **join** with the code + character name & class
6. Start managing currency! 🎲

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

## Project Structure

```
dnd-currency-manager-lan/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (auth, parties, transfers, etc.)
│   │   ├── core/         # Security, config, currency engine, SSE
│   │   ├── models/       # SQLModel database models
│   │   └── schemas/      # Pydantic request/response schemas
│   ├── tests/            # pytest test suite (90 tests)
│   ├── alembic/          # Database migrations
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── app/              # Next.js pages
│   ├── components/       # UI components (shadcn/ui + custom)
│   ├── lib/              # API client, auth context, types
│   ├── hooks/            # Custom React hooks (SSE)
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yaml
├── .env                  # Environment variables (gitignored)
└── .env.example          # Template for .env
```

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

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_USER` | DB username | `dnd_user` |
| `POSTGRES_PASSWORD` | DB password | `dnd_password` |
| `POSTGRES_DB` | Database name | `dnd_currency` |
| `DATABASE_URL` | Full DB connection string | `postgresql://dnd_user:dnd_password@db:5432/dnd_currency` |
| `SECRET_KEY` | JWT signing key | (change in production!) |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `NEXT_PUBLIC_API_URL` | API URL for frontend | `http://localhost:8000` |
