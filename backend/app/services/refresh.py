from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AnalysisResult, RefreshRun, Repository
from app.schemas import (
    AnalysisResponse,
    LanguageStat,
    RefreshHistoryResponse,
    RefreshRunResponse,
    RepositoryResponse,
    TrendingResponse,
    TrendingStatsResponse,
)
from app.services.llm import LlmConfigError, LlmRequestError, analyze_repositories
from app.services.settings import get_or_create_settings, has_valid_llm_config, to_settings_response
from app.services.trending import build_trending_url, enrich_repositories_with_details, fetch_trending_html, parse_trending_html


def refresh_trending(db: Session, since: str | None = None, language: str | None = None) -> TrendingResponse:
    settings = get_or_create_settings(db)
    effective_since = since or settings.default_since
    effective_language = language if language is not None else settings.default_language
    source_url = build_trending_url(effective_since, effective_language)
    run = RefreshRun(source_url=source_url, since=effective_since, language=effective_language, status="running")
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        html = fetch_trending_html(source_url)
        parsed_repos = parse_trending_html(html, settings.max_repositories_per_refresh)
        parsed_repos = enrich_repositories_with_details(parsed_repos)
        repositories = [_upsert_repository(db, parsed, run.id) for parsed in parsed_repos]
        db.commit()
        analysis_failed = _analyze_repositories_for_run(db, settings, run, repositories)
        run.status = "partial_success" if analysis_failed else "success"
        run.error_message = "Some LLM analyses failed" if analysis_failed else None
    except Exception as exc:  # keep external-source failures visible to callers
        db.rollback()
        run = db.get(RefreshRun, run.id) or run
        run.status = "failed"
        run.error_message = str(exc)
    finally:
        run.finished_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
        db.refresh(run)
    return get_trending_response(db)


def analyze_latest(db: Session, since: str | None = None, language: str | None = None) -> TrendingResponse:
    settings = get_or_create_settings(db)
    run = _latest_run(db, since, language)
    if run is None:
        return get_trending_response(db, since, language)
    repositories = _repositories_for_run(db, run.id)
    _analyze_repositories_for_run(db, settings, run, repositories)
    db.add(run)
    db.commit()
    return get_trending_response(db, since, language)


def get_trending_response(
    db: Session, since: str | None = None, language: str | None = None, run_id: int | None = None
) -> TrendingResponse:
    settings = get_or_create_settings(db)
    run = db.get(RefreshRun, run_id) if run_id is not None else _latest_run(db, since, language)
    repositories = _repositories_for_run(db, run.id) if run else []
    return TrendingResponse(
        repositories=[_repository_response(db, repo, run.id if run else None) for repo in repositories],
        latest_run=_run_response(run) if run else None,
        settings=to_settings_response(settings),
    )


def get_refresh_history(db: Session, limit: int = 20) -> RefreshHistoryResponse:
    runs = list(db.scalars(select(RefreshRun).order_by(desc(RefreshRun.id)).limit(limit)))
    return RefreshHistoryResponse(runs=[_run_response(run) for run in runs])


def get_stats(
    db: Session, since: str | None = None, language: str | None = None, run_id: int | None = None
) -> TrendingStatsResponse:
    run = db.get(RefreshRun, run_id) if run_id is not None else _latest_run(db, since, language)
    repositories = _repositories_for_run(db, run.id) if run else []
    language_counts = Counter(repo.language or "Unknown" for repo in repositories)
    return TrendingStatsResponse(
        repository_count=len(repositories),
        language_distribution=[LanguageStat(language=key, count=value) for key, value in language_counts.most_common()],
    )


def _upsert_repository(db: Session, parsed, run_id: int) -> Repository:
    repo = db.scalar(select(Repository).where(Repository.owner == parsed.owner, Repository.name == parsed.name))
    if repo is None:
        repo = Repository(owner=parsed.owner, name=parsed.name, url=parsed.url, rank=parsed.rank)
    repo.url = parsed.url
    repo.description = parsed.description
    repo.detail_description = parsed.detail_description
    repo.topics = json.dumps(parsed.topics, ensure_ascii=False) if parsed.topics else None
    repo.readme_excerpt = parsed.readme_excerpt
    repo.language = parsed.language
    repo.stars = parsed.stars
    repo.forks = parsed.forks
    repo.stars_today = parsed.stars_today
    repo.rank = parsed.rank
    repo.last_seen_run_id = run_id
    db.add(repo)
    db.flush()
    return repo


def _analyze_repositories_for_run(db: Session, settings, run: RefreshRun, repositories: list[Repository]) -> bool:
    if not has_valid_llm_config(settings):
        run.ai_summary_status = "config_error"
        run.ai_summary = None
        run.ai_summary_error = "LLM settings are incomplete"
        for repo in repositories:
            _save_analysis(db, run.id, repo.id, "config_error", error_message="LLM settings are incomplete")
        db.commit()
        return True

    try:
        batch = analyze_repositories(settings, repositories)
    except (LlmConfigError, LlmRequestError) as exc:
        run.ai_summary_status = "failed"
        run.ai_summary = None
        run.ai_summary_error = str(exc)
        for repo in repositories:
            _save_analysis(db, run.id, repo.id, "failed", error_message=str(exc))
        db.commit()
        return True

    run.ai_summary_status = "success"
    run.ai_summary = batch.overall_summary
    run.ai_summary_error = None
    had_failure = False
    for repo in repositories:
        analysis = batch.repositories.get(_repo_key(repo))
        if analysis is None:
            had_failure = True
            _save_analysis(db, run.id, repo.id, "failed", error_message="LLM batch response did not include this repository")
            continue
        _save_analysis(
            db,
            run.id,
            repo.id,
            "success",
            summary=analysis.summary,
            category=analysis.category,
            reasons=analysis.reasons,
        )
    db.commit()
    if had_failure:
        run.ai_summary_status = "partial_success"
        run.ai_summary_error = "LLM batch response was missing one or more repositories"
    return had_failure


def _save_analysis(
    db: Session,
    run_id: int,
    repository_id: int,
    status: str,
    summary: str | None = None,
    category: str | None = None,
    reasons: str | None = None,
    error_message: str | None = None,
) -> None:
    db.add(
        AnalysisResult(
            run_id=run_id,
            repository_id=repository_id,
            status=status,
            summary=summary,
            category=category,
            reasons=reasons,
            error_message=error_message,
        )
    )


def _latest_run(db: Session, since: str | None = None, language: str | None = None) -> RefreshRun | None:
    query = select(RefreshRun)
    if since:
        query = query.where(RefreshRun.since == since)
    if language is not None:
        query = query.where(RefreshRun.language == language)
    return db.scalar(query.order_by(desc(RefreshRun.id)).limit(1))


def _repositories_for_run(db: Session, run_id: int) -> list[Repository]:
    repositories = list(
        db.scalars(
            select(Repository)
            .join(AnalysisResult, AnalysisResult.repository_id == Repository.id)
            .where(AnalysisResult.run_id == run_id)
            .distinct()
            .order_by(Repository.rank)
        )
    )
    if repositories:
        return repositories
    return list(db.scalars(select(Repository).where(Repository.last_seen_run_id == run_id).order_by(Repository.rank)))


def _latest_analysis(db: Session, repository_id: int, run_id: int | None) -> AnalysisResult | None:
    query = select(AnalysisResult).where(AnalysisResult.repository_id == repository_id)
    if run_id is not None:
        query = query.where(AnalysisResult.run_id == run_id)
    return db.scalar(query.order_by(desc(AnalysisResult.id)).limit(1))


def _repository_response(db: Session, repo: Repository, run_id: int | None) -> RepositoryResponse:
    analysis = _latest_analysis(db, repo.id, run_id)
    return RepositoryResponse(
        id=repo.id,
        owner=repo.owner,
        name=repo.name,
        url=repo.url,
        description=repo.description,
        detail_description=repo.detail_description,
        topics=_decode_topics(repo.topics),
        readme_excerpt=repo.readme_excerpt,
        language=repo.language,
        stars=repo.stars,
        forks=repo.forks,
        stars_today=repo.stars_today,
        rank=repo.rank,
        analysis=_analysis_response(analysis) if analysis else None,
    )


def _analysis_response(analysis: AnalysisResult) -> AnalysisResponse:
    return AnalysisResponse(
        status=analysis.status,
        summary=analysis.summary,
        category=analysis.category,
        reasons=analysis.reasons,
        error_message=analysis.error_message,
        created_at=analysis.created_at,
    )


def _run_response(run: RefreshRun) -> RefreshRunResponse:
    return RefreshRunResponse(
        id=run.id,
        source_url=run.source_url,
        since=run.since,
        language=run.language,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        error_message=run.error_message,
        ai_summary_status=run.ai_summary_status,
        ai_summary=run.ai_summary,
        ai_summary_error=run.ai_summary_error,
    )


def _decode_topics(raw_topics: str | None) -> list[str]:
    if not raw_topics:
        return []
    try:
        parsed = json.loads(raw_topics)
    except ValueError:
        return [topic.strip() for topic in raw_topics.split(",") if topic.strip()]
    if isinstance(parsed, list):
        return [str(topic).strip() for topic in parsed if str(topic).strip()]
    return []


def _repo_key(repo: Repository) -> str:
    return f"{repo.owner}/{repo.name}".lower()
