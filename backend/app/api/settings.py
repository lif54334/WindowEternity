from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.scheduler import reschedule_refresh_job
from app.schemas import SettingsResponse, SettingsUpdate
from app.services.settings import get_or_create_settings, to_settings_response, update_settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsResponse)
def read_settings(db: Session = Depends(get_db)) -> SettingsResponse:
    return to_settings_response(get_or_create_settings(db))


@router.put("", response_model=SettingsResponse)
def save_settings(payload: SettingsUpdate, db: Session = Depends(get_db)) -> SettingsResponse:
    settings = update_settings(db, payload)
    reschedule_refresh_job()
    return to_settings_response(settings)
