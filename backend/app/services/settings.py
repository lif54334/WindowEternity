from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Settings
from app.schemas import SettingsResponse, SettingsUpdate

SETTINGS_ID = 1


def get_or_create_settings(db: Session) -> Settings:
    settings = db.get(Settings, SETTINGS_ID)
    if settings is None:
        settings = Settings(id=SETTINGS_ID)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


def to_settings_response(settings: Settings) -> SettingsResponse:
    return SettingsResponse(
        auto_refresh_enabled=settings.auto_refresh_enabled,
        refresh_interval_minutes=settings.refresh_interval_minutes,
        refresh_time_of_day=settings.refresh_time_of_day,
        default_since=settings.default_since,  # type: ignore[arg-type]
        default_language=settings.default_language,
        max_repositories_per_refresh=settings.max_repositories_per_refresh,
        font_size_percent=settings.font_size_percent,
        llm_base_url=settings.llm_base_url,
        llm_model=settings.llm_model,
        llm_timeout_seconds=settings.llm_timeout_seconds,
        llm_custom_prompt=settings.llm_custom_prompt,
        has_llm_api_key=bool(settings.llm_api_key),
        updated_at=settings.updated_at,
    )


def update_settings(db: Session, payload: SettingsUpdate) -> Settings:
    settings = get_or_create_settings(db)
    settings.auto_refresh_enabled = payload.auto_refresh_enabled
    settings.refresh_interval_minutes = payload.refresh_interval_minutes
    settings.refresh_time_of_day = payload.refresh_time_of_day
    settings.default_since = payload.default_since
    settings.default_language = payload.default_language
    settings.max_repositories_per_refresh = payload.max_repositories_per_refresh
    settings.font_size_percent = payload.font_size_percent
    settings.llm_base_url = payload.llm_base_url
    settings.llm_model = payload.llm_model
    settings.llm_timeout_seconds = payload.llm_timeout_seconds
    settings.llm_custom_prompt = payload.llm_custom_prompt
    if payload.llm_api_key:
        settings.llm_api_key = payload.llm_api_key
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def has_valid_llm_config(settings: Settings) -> bool:
    return bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model)
