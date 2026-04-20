from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid

from api_shared import vtstorage, vtlog, config, decode_token, get_current_user, \
    _cleanup_expired_challenges, hash_password, verify_password, create_token, \
    USERS_COLLECTION, CHALLENGE_TTL_SECONDS, _challenges
from data_models import EmailRequest, ChallengeResponse, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/challenge", response_model=ChallengeResponse)
async def request_challenge(req: EmailRequest):
    _cleanup_expired_challenges()
    email = req.email.strip().lower()
    user = vtstorage.get_one(collection=USERS_COLLECTION, query={"email": email})
    challenge_id = str(uuid.uuid4())
    if not user:
        _challenges[challenge_id] = {"email": email, "created_at": datetime.now(timezone.utc), "fake": True}
    else:
        _challenges[challenge_id] = {"email": email, "created_at": datetime.now(timezone.utc)}
    vtlog.info("auth_challenge_created", email=email)
    return {"challengeId": challenge_id}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    _cleanup_expired_challenges()
    challenge = _challenges.pop(req.challengeId, None)
    if not challenge:
        raise HTTPException(status_code=401, detail="Invalid or expired challenge")
    age = (datetime.now(timezone.utc) - challenge["created_at"]).total_seconds()
    if age > CHALLENGE_TTL_SECONDS:
        raise HTTPException(status_code=401, detail="Challenge expired")
    if challenge.get("fake"):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    email = challenge["email"]
    user = vtstorage.get_one(collection=USERS_COLLECTION, query={"email": email})
    if not user or not verify_password(req.password, user.get("password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token(user["_id"], email)
    return {"token": token, "email": email, "userId": user["_id"]}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {
        "email": user.get("email"),
        "userId": user["_id"],
        "role": user.get("role", "agent"),
        "name": user.get("name", ""),
    }
