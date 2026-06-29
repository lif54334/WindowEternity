from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from app.core.config import DEFAULT_USER_AGENT, GITHUB_TRENDING_BASE_URL

VALID_SINCE = {"daily", "weekly", "monthly"}
README_EXCERPT_LIMIT = 1800


@dataclass(slots=True)
class ParsedRepository:
    owner: str
    name: str
    url: str
    description: str | None
    language: str | None
    stars: int | None
    forks: int | None
    stars_today: int | None
    rank: int
    detail_description: str | None = None
    topics: list[str] = field(default_factory=list)
    readme_excerpt: str | None = None


@dataclass(slots=True)
class RepositoryDetails:
    detail_description: str | None = None
    topics: list[str] = field(default_factory=list)
    readme_excerpt: str | None = None


class TrendingFetchError(RuntimeError):
    pass


class TrendingParseError(RuntimeError):
    pass


def build_trending_url(since: str = "daily", language: str | None = None) -> str:
    if since not in VALID_SINCE:
        raise ValueError(f"Unsupported trending range: {since}")
    path = GITHUB_TRENDING_BASE_URL
    if language:
        slug = quote(language.strip().lower().replace(" ", "-"), safe="+")
        path = f"{path}/{slug}"
    return f"{path}?since={since}"


def fetch_trending_html(url: str, timeout_seconds: int = 30) -> str:
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html"})
            response.raise_for_status()
            return response.text
    except httpx.HTTPError as exc:
        raise TrendingFetchError(f"Failed to fetch GitHub Trending: {exc}") from exc


def parse_trending_html(html: str, limit: int) -> list[ParsedRepository]:
    soup = BeautifulSoup(html, "html.parser")
    articles = soup.select("article.Box-row")
    if not articles:
        raise TrendingParseError("GitHub Trending parser found no repository cards")

    repositories: list[ParsedRepository] = []
    for rank, article in enumerate(articles[:limit], start=1):
        title_link = article.select_one("h2 a")
        if title_link is None:
            continue
        href = title_link.get("href", "").strip()
        parts = [part for part in href.split("/") if part]
        if len(parts) < 2:
            continue
        owner, name = parts[0], parts[1]
        description_node = article.select_one("p")
        description = _clean_text(description_node.get_text(" ")) if description_node else None
        language_node = article.select_one('[itemprop="programmingLanguage"]')
        language = _clean_text(language_node.get_text(" ")) if language_node else None
        stars, forks = _parse_star_and_fork_counts(article)
        stars_today = _parse_stars_today(article)
        repositories.append(
            ParsedRepository(
                owner=owner,
                name=name,
                url=f"https://github.com/{owner}/{name}",
                description=description,
                language=language,
                stars=stars,
                forks=forks,
                stars_today=stars_today,
                rank=rank,
            )
        )
    if not repositories:
        raise TrendingParseError("GitHub Trending parser could not normalize any repository cards")
    return repositories


def enrich_repositories_with_details(repositories: list[ParsedRepository], timeout_seconds: int = 30) -> list[ParsedRepository]:
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Accept": "text/html"}
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True, headers=headers) as client:
        for repository in repositories:
            try:
                response = client.get(repository.url)
                response.raise_for_status()
            except httpx.HTTPError:
                continue
            details = parse_repository_detail_html(response.text, repository.owner, repository.name)
            repository.detail_description = details.detail_description
            repository.topics = details.topics
            repository.readme_excerpt = details.readme_excerpt
    return repositories


def parse_repository_detail_html(html: str, owner: str, name: str) -> RepositoryDetails:
    soup = BeautifulSoup(html, "html.parser")
    detail_description = _detail_description(soup, owner, name)
    topics = [_clean_text(node.get_text(" ")) for node in soup.select("a.topic-tag")]
    topics = [topic for topic in topics if topic]
    readme_excerpt = _readme_excerpt(soup)
    return RepositoryDetails(
        detail_description=detail_description,
        topics=topics[:12],
        readme_excerpt=readme_excerpt,
    )


def _detail_description(soup: BeautifulSoup, owner: str, name: str) -> str | None:
    for selector in ('[data-testid="repository-about-description"]', "p.f4.my-3", ".BorderGrid-cell p"):
        node = soup.select_one(selector)
        if node:
            text = _clean_text(node.get_text(" "))
            if text:
                return text

    meta = soup.select_one('meta[name="description"]')
    content = meta.get("content", "") if meta else ""
    text = _clean_text(content)
    prefix = f"GitHub - {owner}/{name}:"
    if text.startswith(prefix):
        text = _clean_text(text[len(prefix):])
    return text or None


def _readme_excerpt(soup: BeautifulSoup) -> str | None:
    readme = soup.select_one("article.markdown-body")
    if not readme:
        return None
    for removable in readme.select("script, style, clipboard-copy"):
        removable.decompose()
    text = _clean_text(readme.get_text(" "))
    if not text:
        return None
    return text[:README_EXCERPT_LIMIT]


def _parse_star_and_fork_counts(article) -> tuple[int | None, int | None]:
    counts: list[int] = []
    for link in article.select('a[href$="/stargazers"], a[href$="/forks"]'):
        parsed = _parse_int(link.get_text(" "))
        if parsed is not None:
            counts.append(parsed)
    stars = counts[0] if len(counts) >= 1 else None
    forks = counts[1] if len(counts) >= 2 else None
    return stars, forks


def _parse_stars_today(article) -> int | None:
    text = _clean_text(article.get_text(" "))
    match = re.search(r"([\d,]+)\s+stars?\s+today", text, flags=re.IGNORECASE)
    if not match:
        return None
    return _parse_int(match.group(1))


def _parse_int(value: str) -> int | None:
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
