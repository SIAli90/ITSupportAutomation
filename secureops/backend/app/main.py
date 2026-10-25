"""Secure IT Operations API (all endpoints except /api/health require login)."""

import json
import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import current_user, hash_password, make_token, require_roles, verify_password
from .config import signing_key
from .db import Base, get_db, get_engine
from .models import Asset, AuditLog, Incident, User
from .schemas import (
    AssetCreate, AssetOut, AssetUpdate, AuditOut, DashboardOut, IncidentCreate,
    IncidentOut, IncidentUpdate, LoginIn, TokenOut, UserCreate, UserOut,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    signing_key()  # Fail fast rather than running with a default/insecure key.
    Base.metadata.create_all(bind=get_engine())
    admin_email = os.getenv("ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "")
    if admin_email or admin_password:
        if not admin_email or len(admin_password) < 12 or admin_password.startswith("CHANGE_ME_"):
            raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD (12+ chars) must both be set")
        with Session(get_engine()) as db:
            if not db.scalar(select(User).where(User.email == admin_email)):
                db.add(User(email=admin_email, full_name="System Administrator", role="admin", password_hash=hash_password(admin_password)))
                db.commit()
    yield


app = FastAPI(title="Secure IT Operations API", version="1.0.0", lifespan=lifespan)
origins = [s.strip() for s in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if s.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type"])


def record(db: Session, actor: User, action: str, resource_type: str, obj_id: int, changes: dict):
    # Log only changed non-sensitive business fields. Passwords and tokens are excluded.
    db.add(AuditLog(actor_user_id=actor.id, actor_email=actor.email, action=action,
                    resource_type=resource_type, resource_id=obj_id,
                    details=json.dumps(changes, default=str)))


def get_or_404(db: Session, model, obj_id: int):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(404, "Record not found")
    return obj


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenOut(access_token=make_token(user))


@app.get("/api/auth/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return user


@app.get("/api/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db), _user: User = Depends(current_user)):
    count = lambda statement: db.scalar(statement) or 0
    return DashboardOut(
        total_assets=count(select(func.count()).select_from(Asset)),
        active_assets=count(select(func.count()).select_from(Asset).where(Asset.status == "active")),
        open_incidents=count(select(func.count()).select_from(Incident).where(Incident.status != "resolved")),
        critical_incidents=count(select(func.count()).select_from(Incident).where(Incident.severity == "critical", Incident.status != "resolved")),
        recent_incidents=list(db.scalars(select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc()).limit(5))),
        recent_audit=list(db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).limit(5))),
    )


@app.get("/api/assets", response_model=list[AssetOut])
def list_assets(search: str = Query("", max_length=120), limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0),
                db: Session = Depends(get_db), _user: User = Depends(current_user)):
    statement = select(Asset)
    if search:
        pattern = f"%{search}%"
        statement = statement.where(Asset.name.ilike(pattern) | Asset.tag.ilike(pattern))
    return db.scalars(statement.order_by(Asset.id.desc()).offset(offset).limit(limit)).all()


@app.post("/api/assets", response_model=AssetOut, status_code=201)
def create_asset(data: AssetCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "analyst"))):
    asset = Asset(**data.model_dump())
    db.add(asset)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Asset tag already exists") from None
    record(db, user, "created", "asset", asset.id, data.model_dump())
    db.commit()
    db.refresh(asset)
    return asset


@app.patch("/api/assets/{asset_id}", response_model=AssetOut)
def update_asset(asset_id: int, data: AssetUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "analyst"))):
    asset = get_or_404(db, Asset, asset_id)
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(asset, field, value)
    if changes:
        record(db, user, "updated", "asset", asset.id, changes)
        db.commit()
        db.refresh(asset)
    return asset


@app.get("/api/incidents", response_model=list[IncidentOut])
def list_incidents(search: str = Query("", max_length=120), limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0),
                   db: Session = Depends(get_db), _user: User = Depends(current_user)):
    statement = select(Incident)
    if search:
        statement = statement.where(Incident.title.ilike(f"%{search}%"))
    return db.scalars(statement.order_by(Incident.id.desc()).offset(offset).limit(limit)).all()


def check_asset(db: Session, asset_id: int | None):
    if asset_id is not None and db.get(Asset, asset_id) is None:
        raise HTTPException(422, "Referenced asset does not exist")


@app.post("/api/incidents", response_model=IncidentOut, status_code=201)
def create_incident(data: IncidentCreate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "analyst"))):
    check_asset(db, data.asset_id)
    incident = Incident(**data.model_dump(), created_by_id=user.id)
    db.add(incident)
    db.flush()
    record(db, user, "created", "incident", incident.id, data.model_dump())
    db.commit()
    db.refresh(incident)
    return incident


@app.patch("/api/incidents/{incident_id}", response_model=IncidentOut)
def update_incident(incident_id: int, data: IncidentUpdate, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "analyst"))):
    incident = get_or_404(db, Incident, incident_id)
    changes = data.model_dump(exclude_unset=True)
    if "asset_id" in changes:
        check_asset(db, changes["asset_id"])
    for field, value in changes.items():
        setattr(incident, field, value)
    if changes:
        record(db, user, "updated", "incident", incident.id, changes)
        db.commit()
        db.refresh(incident)
    return incident


@app.get("/api/audit", response_model=list[AuditOut])
def list_audit(limit: int = Query(100, ge=1, le=200), offset: int = Query(0, ge=0),
               db: Session = Depends(get_db), _user: User = Depends(current_user)):
    return db.scalars(select(AuditLog).order_by(AuditLog.id.desc()).offset(offset).limit(limit)).all()


@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _user: User = Depends(require_roles("admin"))):
    return db.scalars(select(User).order_by(User.id)).all()


@app.post("/api/users", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db), actor: User = Depends(require_roles("admin"))):
    email = str(data.email).lower()
    user = User(email=email, full_name=data.full_name, role=data.role, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Email already exists") from None
    record(db, actor, "created", "user", user.id, {"email": email, "role": data.role})
    db.commit()
    db.refresh(user)
    return user
