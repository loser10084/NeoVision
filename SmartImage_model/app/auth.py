from redis import Redis
from . import config

redis_client = Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    db=config.REDIS_DB,
    password=config.REDIS_PASSWORD,
    decode_responses=True,
)


def get_user_id(token: str):
    if not token:
        return None
    return redis_client.get(f"{config.TOKEN_KEY_PREFIX}{token}")


def require_auth(request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, {"error": "missing auth token"}, 401
    token = auth_header[7:].strip()
    user_id = get_user_id(token)
    if not user_id:
        return None, {"error": "invalid token"}, 401
    return user_id, None, None
