from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    auto_refresh_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    refresh_interval_minutes: Mapped[int] = mapped_column(Integer, default=360, nullable=False)
    refresh_time_of_day: Mapped[str] = mapped_column(String(5), default="09:00", nullable=False)
    default_since: Mapped[str] = mapped_column(String(16), default="daily", nullable=False)
    default_language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    max_repositories_per_refresh: Mapped[int] = mapped_column(Integer, default=25, nullable=False)
    font_size_percent: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    llm_base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    llm_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(200), nullable=True)
    llm_timeout_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    llm_custom_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class RefreshRun(Base):
    __tablename__ = "refresh_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    since: Mapped[str] = mapped_column(String(16), nullable=False)
    language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="running", nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_summary_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    analyses: Mapped[list["AnalysisResult"]] = relationship(back_populates="run")


class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("owner", "name", name="uq_repository_owner_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    detail_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    topics: Mapped[str | None] = mapped_column(Text, nullable=True)
    readme_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(80), nullable=True)
    stars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    forks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stars_today: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    last_seen_run_id: Mapped[int | None] = mapped_column(ForeignKey("refresh_runs.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    analyses: Mapped[list["AnalysisResult"]] = relationship(back_populates="repository")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("refresh_runs.id"), nullable=False)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    run: Mapped[RefreshRun] = relationship(back_populates="analyses")
    repository: Mapped[Repository] = relationship(back_populates="analyses")