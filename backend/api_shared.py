import sys
import os
from vtutils.confparser import env_config, parse_config
from vtutils.misc import get_project_root
from vtutils.vtlogger import initLog, getLog
from vtstorage.perm_storage import VTPermStorage

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import bcrypt
from datetime import datetime, timedelta, timezone

bearer_scheme = HTTPBearer()

ROOT_DIR = get_project_root()
sys.path.append(ROOT_DIR)

package_name = "wa_crm_api"
vtlog = initLog(package_name)

config = env_config("{0}/.env".format(ROOT_DIR))
configuration = parse_config("all.ini", config)

vtstorage = VTPermStorage(
    configuration["env_config"]["PERMANENT_STORAGE"],
    configuration["mongodb"],
    params={"database": configuration["env_config"]["PERMANENT_DB"]}
)

USERS_COLLECTION = "users"
CONTACTS_COLLECTION = "contacts"
CONVERSATIONS_COLLECTION = "conversations"
MESSAGES_COLLECTION = "messages"
TASKS_COLLECTION = "tasks"
AUTOMATIONS_COLLECTION = "automations"
TEMPLATES_COLLECTION = "templates"
SETTINGS_COLLECTION = "settings"
MODULES_COLLECTION = "modules"
ACTIVITY_LOG_COLLECTION = "activity_log"

JWT_SECRET = config.get("JWT_SECRET", "wacrm-jwt-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

_challenges: dict[str, dict] = {}
CHALLENGE_TTL_SECONDS = 300


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    payload = decode_token(credentials.credentials)
    user = vtstorage.get_one(collection=USERS_COLLECTION, query={"_id": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _cleanup_expired_challenges():
    now = datetime.now(timezone.utc)
    expired = [k for k, v in _challenges.items()
               if (now - v["created_at"]).total_seconds() > CHALLENGE_TTL_SECONDS]
    for k in expired:
        _challenges.pop(k, None)
