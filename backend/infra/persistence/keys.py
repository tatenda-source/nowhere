from uuid import UUID

class RedisKeys:
    @staticmethod
    def intent(intent_id: UUID | str) -> str:
        return f"intent:{str(intent_id)}"

    @staticmethod
    def intent_geo() -> str:
        return "intents:geo" # Global geo index

    @staticmethod
    def intent_messages(intent_id: UUID | str) -> str:
        return f"intent:{str(intent_id)}:msgs"

    @staticmethod
    def intent_joins(intent_id: UUID | str) -> str:
        return f"intent:{str(intent_id)}:joins" # Set of user_ids

    @staticmethod
    def intent_flags(intent_id: UUID | str) -> str:
        return f"intent:{str(intent_id)}:flaggers"  # Set of user_ids who flagged

    @staticmethod
    def rate_limit(user_id: str, action: str) -> str:
        return f"identity:{user_id}:limits:{action}"

    @staticmethod
    def user_intents(user_id: str) -> str:
        return f"user:{user_id}:intents"

    @staticmethod
    def area_hash(geohash: str) -> str:
        return f"area:{geohash}"

    @staticmethod
    def spam_last_hash(user_id: str) -> str:
        return f"spam:{user_id}:last_hash"

    @staticmethod
    def expiry_queue() -> str:
        return "sys:expiry_queue"
