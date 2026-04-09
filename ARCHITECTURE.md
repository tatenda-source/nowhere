# Nowhere — Architecture Document

> Ephemeral, location-scoped, anonymous coordination platform.
> Everything is transient. 24-hour TTL. No accounts. No history.

---

## 1. System Overview

```
                 ┌─────────────────────────────┐
                 │     React Native (Expo)      │
                 │     iOS / Android / Web      │
                 └──────────────┬───────────────┘
                                │
                    HTTPS (REST + WebSocket)
                                │
                 ┌──────────────▼───────────────┐
                 │        Caddy Proxy            │
                 │   Auto-TLS / HSTS / Headers   │
                 │      Port 80 → 443            │
                 └──────────────┬───────────────┘
                                │
                 ┌──────────────▼───────────────┐
                 │     FastAPI (Python 3.13)     │
                 │    Auth │ API │ WebSocket     │
                 └──┬───────────────────────┬───┘
                    │                       │
         ┌──────────▼──────────┐  ┌─────────▼─────────┐
         │   Redis 7 (Primary) │  │ PostgreSQL 15 (Opt)│
         │  Geo │ TTL │ Stream │  │   Aggregate Metrics│
         └─────────────────────┘  └────────────────────┘
```

**Stack:** FastAPI + Redis + React Native (Expo) + Caddy + Docker Compose

**Key Principle:** All user data expires in 24 hours. No PII in metrics. Anonymous by design.

---

## 2. Directory Structure

```
nowhere/
├── app/                            # React Native / Expo frontend
│   ├── App.tsx                     # Root navigator + ErrorBoundary
│   ├── screens/
│   │   ├── HomeScreen.tsx          # Nearby intents list
│   │   ├── CreateScreen.tsx        # New intent modal
│   │   └── ChatScreen.tsx          # Real-time messaging (WS + polling)
│   ├── hooks/
│   │   ├── useIntents.ts           # Orchestrator: location → fetch → join
│   │   ├── useLocation.ts          # expo-location wrapper
│   │   ├── useNearbyIntents.ts     # API fetch + stale data retention
│   │   └── useJoinIntent.ts        # Join action + UUID validation
│   ├── utils/
│   │   ├── config.ts               # API_URL resolution (env/platform)
│   │   ├── api.ts                  # Axios + JWT interceptor + 401 retry
│   │   ├── identity.ts             # SecureStore UUID + JWT + expiry check
│   │   ├── location.ts             # GPS with 3dp privacy rounding
│   │   ├── validation.ts           # UUID regex + display sanitizer
│   │   └── logger.ts               # Safe logging (no tokens in prod)
│   ├── types/intent.ts             # Intent interface
│   └── i18n/                       # Internationalization (English)
│
├── backend/                        # FastAPI Python backend
│   ├── main.py                     # App setup, middleware, lifespan
│   ├── config.py                   # Settings + secret validation
│   ├── spam.py                     # Heuristic spam detection
│   ├── api/                        # HTTP handlers (thin)
│   │   ├── intents.py              # CRUD + nearby + clusters + flag
│   │   ├── auth.py                 # Handshake + GDPR erasure
│   │   ├── ws.py                   # WebSocket + ConnectionManager
│   │   ├── metrics.py              # /metrics (localhost only)
│   │   ├── limiter.py              # Per-user rate limiting
│   │   ├── schemas.py              # Request/response validation
│   │   ├── deps.py                 # Dependency injection
│   │   └── debug.py                # Seed endpoint (DEBUG only)
│   ├── auth/
│   │   ├── jwt.py                  # JWT create/decode (HS256, iss/aud)
│   │   └── middleware.py           # Bearer auth + ephemeral fallback
│   ├── core/                       # Domain layer (DDD)
│   │   ├── models/
│   │   │   ├── intent.py           # Aggregate root (visibility, flags)
│   │   │   ├── message.py          # Message (HTML-escaped content)
│   │   │   └── ranking.py          # Scoring formula
│   │   ├── commands.py             # Write operations
│   │   ├── events.py               # Domain events (no GPS)
│   │   ├── event_bus.py            # Parallel async dispatch
│   │   ├── unit_of_work.py         # Transaction protocol
│   │   └── exceptions.py           # Domain errors
│   ├── services/
│   │   ├── intent_command_handler.py  # Write path (UoW)
│   │   ├── intent_query_service.py    # Read path (ranking)
│   │   ├── ranking_service.py         # Configurable scoring
│   │   ├── clustering_service.py      # Zoom-aware geo clustering
│   │   └── metrics_event_handler.py   # Event → aggregate metrics
│   ├── infra/persistence/
│   │   ├── redis.py                # Connection pool + retry + timeouts
│   │   ├── intent_repo.py          # Geo search + TTL + Lua scripts
│   │   ├── join_repo.py            # Atomic Lua join
│   │   ├── message_repo.py         # Capped list + TTL refresh
│   │   ├── event_store.py          # Redis Stream (capped 10k)
│   │   ├── metrics_repo.py         # Postgres (no PII)
│   │   ├── keys.py                 # Redis key schema
│   │   ├── lua_scripts.py          # ATOMIC_FLAG, SAVE_JOIN
│   │   ├── unit_of_work.py         # Redis pipeline transactions
│   │   └── db.py                   # SQLAlchemy async engine
│   └── security/device_tokens.py   # HMAC device token signing
│
├── infra/proxy/Caddyfile           # Reverse proxy + TLS + headers
├── docker-compose.yml              # Full stack (4 services, 2 networks)
├── .env.example                    # Required env vars template
├── .dockerignore                   # Slim Docker builds
└── .github/workflows/ci.yml       # CI pipeline
```

---

## 3. Architecture Patterns

### CQRS (Command Query Responsibility Segregation)
- **Write path:** API → Command → IntentCommandHandler → UoW (Redis pipeline) → Event Bus
- **Read path:** API → IntentQueryService → IntentRepository (Redis reader) → RankingService

### Unit of Work
- Redis pipeline wraps all writes atomically
- Events collected during transaction, published after commit
- Rollback resets pipeline and discards events

### Domain-Driven Design
- **Aggregate Root:** Intent (owns joins, messages, flags)
- **Value Objects:** Message, Command, DomainEvent
- **Repository Pattern:** IntentRepository, JoinRepository, MessageRepository
- **Domain Events:** IntentCreated, IntentJoined, MessagePosted, IntentFlagged

### Event Sourcing (Lite)
- Domain events persisted to Redis Stream (`nowhere:events`, capped 10k)
- Event handlers dispatch in parallel via `asyncio.gather`
- Metrics handler consumes events → writes aggregate-only Postgres rows

---

## 4. Data Model (Redis)

| Key Pattern | Type | TTL | Purpose |
|---|---|---|---|
| `intent:{id}` | String (JSON) | 24h | Intent data |
| `intents:geo` | Sorted Set (Geo) | — | Proximity search index |
| `intent:{id}:joins` | Set | 24h | User IDs who joined |
| `intent:{id}:msgs` | List (capped 100) | 24h | Chat messages |
| `intent:{id}:flaggers` | Set | 24h | User IDs who flagged |
| `user:{id}:intents` | Set | 24h | Intents created by user |
| `identity:{id}:limits:{action}` | Counter | 1h | Rate limit windows |
| `spam:{id}:last_hash` | String | 5m | Content dedup hash |
| `nowhere:events` | Stream (10k cap) | — | Domain event log |
| `nowhere:counter:{name}` | Counter | — | Operational metrics |
| `sys:expiry_queue` | Sorted Set | — | Scheduled cleanup |

---

## 5. API Surface

### REST Endpoints

| Method | Path | Auth | Rate Limit | Purpose |
|--------|------|------|------------|---------|
| `POST` | `/auth/handshake` | None | — | Exchange anon_id for JWT |
| `DELETE` | `/auth/me/data` | JWT | — | GDPR erasure |
| `POST` | `/intents/` | JWT | 5/hr | Create intent |
| `GET` | `/intents/nearby` | Any | — | Proximity search |
| `GET` | `/intents/clusters` | Any | — | Zoom-aware clustering |
| `POST` | `/intents/{id}/join` | JWT | 20/hr | Join intent |
| `POST` | `/intents/{id}/messages` | JWT | 100/hr | Post message |
| `POST` | `/intents/{id}/flag` | JWT | 5/hr | Flag intent (deduped) |
| `GET` | `/health` | None | — | Redis connectivity check |
| `GET` | `/metrics` | Localhost | — | Operational counters |

### WebSocket

| Path | Auth | Protocol |
|------|------|----------|
| `/ws/intents/{id}/messages?token={JWT}` | JWT query param | Ping/pong keepalive 30s, timeout 60s |

---

## 6. Authentication Flow

```
Device Boot → getOrCreateIdentity() → UUID (SecureStore / localStorage)
         │
         ├─→ POST /auth/handshake {anon_id: UUID}
         │         │
         │         └─→ JWT {sub: UUID, iss: "nowhere-backend", aud: "nowhere-app", exp: +7d}
         │
         └─→ Axios interceptor attaches "Authorization: Bearer {JWT}" to all requests
              │
              └─→ AuthMiddleware extracts sub, sets request.state.user_id
                   │
                   └─→ Every 30 days: identity rotates (new UUID, new JWT)
```

**No email. No password. No registration. JWT-only trust.**

---

## 7. Security Architecture

### Middleware Stack (order matters)

1. **SecurityHeadersMiddleware** — CSP, HSTS, X-Frame-Options, Permissions-Policy
2. **CORSMiddleware** — Restricted to `ALLOWED_ORIGINS`
3. **AuthMiddleware** — JWT verification, ephemeral fallback
4. **Body Size Limit** — 1MB max request body
5. **Request ID** — Correlation ID propagation

### Defense-in-Depth

| Layer | Protection |
|-------|-----------|
| **Caddy** | Auto-TLS, HSTS, security headers, body size limit |
| **FastAPI** | CSP, CORS, auth, rate limiting, input validation |
| **Domain** | HTML escape, spam detection, flag dedup, membership checks |
| **Redis** | Password auth, connection pooling, Lua atomicity |
| **Docker** | Non-root user, read-only FS, network isolation, resource limits |
| **Client** | UUID validation, sessionStorage for JWT, HTTPS enforcement, safe logging |

### Data Privacy (GDPR)

- No PII in metrics (aggregate geohash only)
- No GPS in domain events
- All user data expires in 24h (Redis TTL)
- `DELETE /auth/me/data` — cascading erasure across all keys
- Coordinates rounded to 3dp (~110m) at model level
- No third-party analytics or tracking

---

## 8. Infrastructure

### Docker Compose Topology

```
                    ┌─────────────┐
                    │   proxy     │ ← Ports 80, 443
                    │  (Caddy 2)  │
                    └──────┬──────┘
                           │ frontend network
                    ┌──────▼──────┐
                    │    api      │ ← Health check: /health
                    │  (FastAPI)  │
                    └──┬──────┬───┘
                       │      │ backend network
              ┌────────▼──┐ ┌─▼────────┐
              │   redis   │ │ postgres  │
              │  (Redis 7)│ │ (PG 15)   │
              └───────────┘ └───────────┘
```

| Service | Memory | CPU | Health Check | Restart |
|---------|--------|-----|-------------|---------|
| redis | 256M | 0.5 | `redis-cli ping` | unless-stopped |
| postgres | 512M | 1.0 | `pg_isready` | unless-stopped |
| api | 512M | 1.0 | `curl /health` | unless-stopped |
| proxy | 128M | 0.5 | depends_on api | unless-stopped |

### Persistence

| Volume | Service | Purpose |
|--------|---------|---------|
| `redis_data` | redis | AOF persistence (appendonly yes) |
| `pgdata` | postgres | Database files |
| `caddy_data` | proxy | TLS certificates |
| `caddy_config` | proxy | Caddy configuration state |

---

## 9. Frontend Architecture

### Navigation

```
NavigationContainer
  └─ NativeStackNavigator
       ├─ Home (default)      ← FlatList of nearby intents
       ├─ Create (modal)      ← Title + emoji form
       └─ Chat (push)         ← WebSocket + polling messages
```

### Hook Composition

```
useIntents (orchestrator)
  ├─ useLocation()          → { location, fetchLocation }
  ├─ useNearbyIntents()     → { nearby, loading, message, fetchIntents }
  └─ useJoinIntent()        → { joinIntent }
```

### Data Flow

```
App Launch
  → useLocation.fetchLocation() → expo-location (3dp rounding)
  → useNearbyIntents.fetchIntents(location) → GET /intents/nearby
  → Display in FlatList

User Creates Intent
  → CreateScreen → getCurrentLocation() → POST /intents/
  → Navigate back → auto-refresh

User Joins Intent
  → useJoinIntent → POST /intents/{id}/join → Alert → refresh

User Opens Chat
  → ChatScreen → validate UUID → getAccessToken()
  → WebSocket connect with JWT query param
  → Fallback: polling every 3s on WS failure
```

---

## 10. Scoring & Ranking

```
score = (W_DIST × distance_score) + (W_FRESH × freshness_score) + (W_POP × popularity_score)

distance_score  = 1 - (distance_km / radius_km)     # closer = higher
freshness_score = 1 - (age_seconds / decay_seconds)  # newer = higher
popularity_score = log(join_count + 1)                # more joins = higher

Defaults: W_DIST=1.0, W_FRESH=2.0, W_POP=0.5 (configurable via env)
```

**Visibility rule:** Unverified intents (0 joins) only visible within 200m.

---

## 11. Deployment Checklist

### Required Before Deploy
- [x] Set `JWT_SECRET`, `DEVICE_TOKEN_SECRET`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` in `.env`
- [x] Set `ALLOWED_ORIGINS` to production domain
- [x] Set `NOWHERE_DOMAIN` for Caddy auto-TLS
- [x] Set `DEBUG=false`
- [x] Docker build passes
- [x] Health checks configured
- [x] Non-root containers
- [x] Network isolation (frontend/backend)
- [x] Resource limits on all services
- [x] Redis persistence enabled (AOF)

### Recommended Post-Deploy
- [ ] Rotate secrets (they exist on dev machine)
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Set up log aggregation
- [ ] Run `npm audit` on frontend deps
- [ ] Penetration test
- [ ] Load test (target: 1000 concurrent connections)

---

## 12. PWA Deployment Gap Analysis

See `PROBLEM_AND_SOLUTION.md` for the full PWA checklist and current status.
