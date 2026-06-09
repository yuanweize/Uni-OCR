import datetime
import pyotp
import jwt
import secrets
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.orm import Session
import bcrypt

from .database import get_db, User, ApiKey, Config

router = APIRouter(prefix="/api", tags=["Auth & Config"])

class LoginRequest(BaseModel):
    password: str
    totp_code: Optional[str] = None

class Setup2FARequest(BaseModel):
    password: str

class Verify2FARequest(BaseModel):
    totp_code: str

class UpdateConfigRequest(BaseModel):
    is_ocr_public: Optional[bool] = None
    new_password: Optional[str] = None

class CreateApiKeyRequest(BaseModel):
    name: str

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode('utf-8'), salt).decode("utf-8")

def get_jwt_secret(db: Session) -> str:
    return db.query(Config).filter(Config.key == "jwt_secret").first().value

def create_access_token(data: dict, db: Session):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(db), algorithm="HS256")
    return encoded_jwt

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    
    # Check if it's an API Key
    if token.startswith("sk-"):
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        api_key = db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True).first()
        if not api_key:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        return {"sub": "api_key", "name": api_key.name}

    # Otherwise it's a JWT
    try:
        payload = jwt.decode(token, get_jwt_secret(db), algorithms=["HS256"])
        if payload.get("sub") != "admin":
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Check if forced password change is required
        admin = db.query(User).filter(User.username == "admin").first()
        if admin.is_initial_setup and payload.get("type") != "setup":
            raise HTTPException(status_code=403, detail="requires_password_change")
            
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_public_or_authenticated(authorization: str = Header(None), db: Session = Depends(get_db)):
    is_public = db.query(Config).filter(Config.key == "is_ocr_public").first()
    if is_public and is_public.value == "true":
        return True
    return get_current_user(authorization, db)

@router.post("/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.username == "admin").first()
    if not verify_password(req.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")
        
    if admin.is_2fa_enabled:
        if not req.totp_code:
            raise HTTPException(status_code=403, detail="2FA required")
        totp = pyotp.TOTP(admin.totp_secret)
        if not totp.verify(req.totp_code):
            raise HTTPException(status_code=401, detail="Invalid 2FA code")
            
    # If initial setup, return special token that can ONLY change password
    token_type = "setup" if admin.is_initial_setup else "access"
    token = create_access_token({"sub": "admin", "type": token_type}, db)
    return {
        "access_token": token, 
        "token_type": "bearer",
        "requires_password_change": admin.is_initial_setup
    }

@router.post("/auth/2fa/setup")
def setup_2fa(req: Setup2FARequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.username == "admin").first()
    if not verify_password(req.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")
        
    secret = pyotp.random_base32()
    admin.totp_secret_pending = secret
    db.commit()
    
    uri = pyotp.totp.TOTP(secret).provisioning_uri(name="Admin", issuer_name="UniOCR")
    return {"secret": secret, "uri": uri}

@router.post("/auth/2fa/verify")
def verify_2fa(req: Verify2FARequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin.totp_secret_pending:
        raise HTTPException(status_code=400, detail="No pending 2FA setup")
        
    totp = pyotp.TOTP(admin.totp_secret_pending)
    if not totp.verify(req.totp_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
    admin.totp_secret = admin.totp_secret_pending
    admin.is_2fa_enabled = True
    admin.totp_secret_pending = None
    db.commit()
    return {"status": "success"}

@router.post("/auth/2fa/disable")
def disable_2fa(req: Setup2FARequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.username == "admin").first()
    if not verify_password(req.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")
        
    admin.totp_secret = None
    admin.is_2fa_enabled = False
    db.commit()
    return {"status": "success"}

@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    is_public = db.query(Config).filter(Config.key == "is_ocr_public").first()
    admin = db.query(User).filter(User.username == "admin").first()
    return {
        "is_ocr_public": is_public.value == "true" if is_public else True,
        "is_2fa_enabled": admin.is_2fa_enabled,
        "requires_password_change": admin.is_initial_setup
    }

@router.post("/config")
def update_config(req: UpdateConfigRequest, authorization: str = Header(None), db: Session = Depends(get_db)):
    # Custom auth check to allow setup token to ONLY change password
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)
    token = authorization.split(" ")[1]
    payload = jwt.decode(token, get_jwt_secret(db), algorithms=["HS256"])
    if payload.get("sub") != "admin":
        raise HTTPException(status_code=401)
        
    admin = db.query(User).filter(User.username == "admin").first()
    
    if req.new_password:
        admin.password_hash = hash_password(req.new_password)
        admin.is_initial_setup = False
        
    if req.is_ocr_public is not None and payload.get("type") != "setup":
        is_public = db.query(Config).filter(Config.key == "is_ocr_public").first()
        is_public.value = "true" if req.is_ocr_public else "false"
        
    db.commit()
    return {"status": "success"}

@router.get("/apikeys")
def list_api_keys(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    keys = db.query(ApiKey).all()
    return [{"id": k.id, "name": k.name, "prefix": k.prefix, "is_active": k.is_active, "created_at": k.created_at} for k in keys]

@router.post("/apikeys")
def create_api_key(req: CreateApiKeyRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    raw_key = "sk-" + secrets.token_hex(24)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    
    new_key = ApiKey(
        key_hash=key_hash,
        name=req.name,
        prefix=raw_key[:8] + "..."
    )
    db.add(new_key)
    db.commit()
    
    return {"api_key": raw_key, "name": new_key.name}

@router.delete("/apikeys/{key_id}")
def delete_api_key(key_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.get("sub") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    
    key = db.query(ApiKey).filter(ApiKey.id == key_id).first()
    if key:
        db.delete(key)
        db.commit()
    return {"status": "success"}
