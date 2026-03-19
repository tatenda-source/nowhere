import uuid
import logging
import traceback
import socket
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Import project modules
from .config import settings
from .core.logging import configure_logging
from .core.exceptions import DomainError, IntentNotFound, InvalidAction, IntentExpired, SpamDetected
from .infra.persistence.redis import lifespan as redis_lifespan, RedisClient
from .infra.persistence.db import init_db
from .api.intents import router as intents_router
from .api.debug import router as debug_router
from .api.auth import router as auth_router
from .auth.middleware import AuthMiddleware

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

# --- UTILS ---
def get_local_ip():
    try:
        # Connect to an external server to determine the local IP used for routing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
logger.info(f"Detected Local LAN IP: {LOCAL_IP}")

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
    
    # Init DB
    try:
        await init_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.error(f"Failed to initialize Database: {e}")

    yield
    await RedisClient.disconnect()

# --- APP SETUP ---
app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

# --- MIDDLEWARE ---

# 1. CORS - Ultra Permissive
# allow_origins=['*'] with credentials=True is technically invalid in spec,
# so we use allow_origin_regex='.*' to match ANY origin while allowing credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex='^http://.*$', # Allow all http origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Auth Middleware
app.add_middleware(AuthMiddleware)

# 3. Request ID logging
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(f"Request started: {request.method} {request.url} - RequestID: {request_id}")
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(f"Request completed: {request.method} {request.url} - RequestID: {request_id}")
        return response
    except Exception as e:
        logger.error(f"Request failed: {request.method} {request.url} - Error: {e}")
        # Re-raise so the global handler catches it
        raise e 

# --- ROUTERS ---
app.include_router(intents_router, prefix="/intents", tags=["intents"])
app.include_router(debug_router, prefix="/debug", tags=["debug"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# --- EXCEPTION HANDLERS ---

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to log full stack traces and return 500 JSON.
    This ensures we never send a raw 500 text body or crash the connection.
    CORS middleware runs before this, so headers should be attached (mostly).
    """
    logger.error(f"Global Exception: {exc}")
    traceback.print_exc() # Print full stack trace to console
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal Server Error",
            "detail": str(exc),
            "type": type(exc).__name__,
            "trace": traceback.format_exc().splitlines()[-3:] # Last 3 lines of trace for client safety
        }
    )

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
    return {
        "status": "ok", 
        "app_name": settings.APP_NAME,
        "local_ip": LOCAL_IP
    }
