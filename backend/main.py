import asyncio
import uuid
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Import project modules
from .config import settings
from .core.logging import configure_logging, request_id_var
from .core.exceptions import DomainError, IntentNotFound, InvalidAction, IntentExpired, SpamDetected
from .infra.persistence.redis import lifespan as redis_lifespan, RedisClient
from .infra.persistence.db import init_db
from .api.intents import router as intents_router
from .api.auth import router as auth_router
from .api.ws import router as ws_router
from .api.metrics import router as metrics_router
from .auth.middleware import AuthMiddleware

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Determine Redis URL from settings or default
    redis_url = getattr(settings, "REDIS_DSN", "redis://localhost:6379")
    try:
        await RedisClient.connect(redis_url)
        logger.info("Redis connected.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # We don't crash here to allow 'partial' start if user wants debugging
    
    # Init DB (optional — only if Postgres is enabled for metrics)
    if settings.POSTGRES_ENABLED:
        try:
            await init_db()
            logger.info("Database initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Database: {e}")
    else:
        logger.info("PostgreSQL disabled — metrics stored in Redis only.")

    yield

    # Graceful shutdown: close all WebSocket connections before disconnecting Redis
    from .api.ws import get_ws_manager
    ws_manager = get_ws_manager()
    for room in list(ws_manager._rooms.values()):
        for ws in list(room):
            try:
                await ws.close(code=1001, reason="Server shutting down")
            except Exception:
                pass
    ws_manager._rooms.clear()
    ws_manager._total = 0

    await RedisClient.disconnect()

# --- APP SETUP ---
app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

# --- SECURITY HEADERS MIDDLEWARE ---

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' wss: ws:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), camera=(), microphone=()"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        return response

# --- MIDDLEWARE ---

# 1. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 2. CORS — restricted to configured origins
_allowed_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()]
if settings.DEBUG and not _allowed_origins:
    # In debug mode, allow localhost origins for development
    _allowed_origins = ["http://localhost:3000", "http://localhost:8081", "http://localhost:19006"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Nowhere-Identity", "X-Request-ID"],
)

# 3. Auth Middleware
app.add_middleware(AuthMiddleware)

# 4. Request body size limit (1MB)
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 1_048_576:
        return JSONResponse(status_code=413, content={"detail": "Request body too large"})
    return await call_next(request)

# 5. Request ID + correlation logging
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    token = request_id_var.set(rid)
    logger.info(f"{request.method} {request.url.path}")
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        logger.info(f"{request.method} {request.url.path} -> {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"{request.method} {request.url.path} failed: {e}")
        raise
    finally:
        request_id_var.reset(token)

# --- ROUTERS ---
app.include_router(intents_router, prefix="/intents", tags=["intents"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(ws_router)
app.include_router(metrics_router)

# Debug routes only available in DEBUG mode
if settings.DEBUG:
    from .api.debug import router as debug_router
    app.include_router(debug_router, prefix="/debug", tags=["debug"])

# --- EXCEPTION HANDLERS ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler. Logs full trace server-side,
    returns only a generic message to the client.
    """
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    content = {"message": "Internal Server Error"}
    if settings.DEBUG:
        content["detail"] = str(exc)
        content["type"] = type(exc).__name__
    return JSONResponse(status_code=500, content=content)

@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    logger.warning(f"Domain Error: {exc}")
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.exception_handler(IntentNotFound)
async def intent_not_found_handler(request: Request, exc: IntentNotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Intent not found"},
    )
    
@app.exception_handler(SpamDetected)
async def spam_handler(request: Request, exc: SpamDetected):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

@app.get("/health")
async def health_check():
    redis_ok = False
    try:
        redis = RedisClient.get_client()
        await asyncio.wait_for(redis.ping(), timeout=2.0)
        redis_ok = True
    except Exception:
        pass
    status = "ok" if redis_ok else "degraded"
    code = 200 if redis_ok else 503
    return JSONResponse(
        status_code=code,
        content={"status": status, "redis": redis_ok},
    )
