from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import uuid
from .jwt import decode_access_token
import logging

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user_id = None

        # Only trust cryptographically signed JWTs for identity
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                user_id = payload["sub"]

        # If no valid JWT, generate a temporary anonymous identity.
        # This identity is ephemeral and per-request — not trusted for ownership.
        if not user_id:
            user_id = str(uuid.uuid4())
            request.state.is_authenticated = False
        else:
            request.state.is_authenticated = True

        # Validate UUID format
        try:
            uuid_obj = uuid.UUID(user_id)
            user_id = str(uuid_obj)
        except ValueError:
            user_id = str(uuid.uuid4())
            request.state.is_authenticated = False

        request.state.user_id = user_id

        response = await call_next(request)

        # Set httponly cookie only for authenticated users on web
        if request.state.is_authenticated:
            response.set_cookie(
                key="user_id",
                value=user_id,
                max_age=7 * 24 * 60 * 60,  # 7 days (matches JWT expiry)
                httponly=True,
                secure=True,
                samesite="lax",
            )

        return response
