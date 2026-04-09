from pydantic import BaseModel


class JoinRequest(BaseModel):
    """Join request body. user_id comes from auth middleware, never the request body."""
    pass
