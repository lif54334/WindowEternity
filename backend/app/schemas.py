from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

SinceValue = Literal["daily", "weekly", "monthly"]


class SettingsBase(BaseModel):
    auto_refresh_enabled: bool = False
    refresh_interval_minutes: int = Field(default=360, ge=5, le=10080)
    refresh_time_of_day: str = Field(default="09:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    default_since: SinceValue = "daily"
    default_language: str | None = None
    max_repositories_per_refresh: int = Field(default=25, ge=1, le=100)
    font_size_percent: int = Field(default=100, ge=80, le=140)
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: int = Field(default=60, ge=5, le=300)
    llm_custom_prompt: str | None = None

    @field_validator("default_language", "llm_base_url", "llm_model", "llm_custom_prompt", mode="before")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


class SettingsUpdate(SettingsBase):
    llm_api_key: str | None = None

    @field_validator("llm_api_key", mode="before")
    @classmethod
    def blank_key_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


class SettingsResponse(SettingsBase):
    has_llm_api_key: bool = False
    updated_at: datetime | None = None


class RefreshRequest(BaseModel):
    since: SinceValue | None = None
    language: str | None = None
    force_analyze: bool = True

    @field_validator("language", mode="before")
    @classmethod
    def blank_language_to_none(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned or None
        return value


class AnalyzeRequest(BaseModel):
    since: SinceValue | None = None
    language: str | None = None


class AnalysisResponse(BaseModel):
    status: str
    summary: str | None = None
    category: str | None = None
    reasons: str | None = None
    error_message: str | None = None
    created_at: datetime | None = None


class RepositoryResponse(BaseModel):
    id: int
    owner: str
    name: str
    url: str
    description: str | None = None
    detail_description: str | None = None
    topics: list[str] = Field(default_factory=list)
    readme_excerpt: str | None = None
    language: str | None = None
    stars: int | None = None
    forks: int | None = None
    stars_today: int | None = None
    rank: int
    analysis: AnalysisResponse | None = None


class RefreshRunResponse(BaseModel):
    id: int
    source_url: str
    since: str
    language: str | None = None
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    ai_summary_status: str | None = None
    ai_summary: str | None = None
    ai_summary_error: str | None = None


class TrendingResponse(BaseModel):
    repositories: list[RepositoryResponse]
    latest_run: RefreshRunResponse | None = None
    settings: SettingsResponse


class RefreshHistoryResponse(BaseModel):
    runs: list[RefreshRunResponse]


class LanguageStat(BaseModel):
    language: str
    count: int


class CategoryStat(BaseModel):
    category: str
    count: int


class TrendingStatsResponse(BaseModel):
    repository_count: int
    language_distribution: list[LanguageStat]
    top_repositories: list[RepositoryResponse]
    category_distribution: list[CategoryStat]


class ErrorResponse(BaseModel):
    detail: str