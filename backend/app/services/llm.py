from __future__ import annotations

import json
from dataclasses import dataclass, field

import httpx

from app.models import Repository, Settings


@dataclass(slots=True)
class LlmAnalysis:
    summary: str
    category: str | None = None
    reasons: str | None = None


@dataclass(slots=True)
class LlmBatchAnalysis:
    overall_summary: str
    repositories: dict[str, LlmAnalysis] = field(default_factory=dict)


class LlmConfigError(RuntimeError):
    pass


class LlmRequestError(RuntimeError):
    pass


def analyze_repositories(settings: Settings, repositories: list[Repository]) -> LlmBatchAnalysis:
    if not settings.llm_base_url or not settings.llm_api_key or not settings.llm_model:
        raise LlmConfigError("LLM base URL, API key, and model are required before analysis can run")
    if not repositories:
        return LlmBatchAnalysis(overall_summary="当前筛选范围没有可分析的仓库。")

    endpoint = _chat_completions_endpoint(settings.llm_base_url)
    prompt = _build_batch_prompt(repositories, settings.llm_custom_prompt)
    payload = {
        "model": settings.llm_model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个技术趋势分析助手。必须用简体中文回答，面向开发者和技术团队，并严格返回可解析 JSON。",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {settings.llm_api_key}", "Content-Type": "application/json"}
    try:
        with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
            response = client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise LlmRequestError(f"LLM request failed: {exc}") from exc

    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise LlmRequestError("LLM response did not contain choices[0].message.content") from exc

    if not content:
        raise LlmRequestError("LLM response was empty")
    return _parse_batch_analysis(content)


def _chat_completions_endpoint(base_url: str) -> str:
    cleaned = base_url.rstrip("/")
    if cleaned.endswith("/chat/completions"):
        return cleaned
    if cleaned.endswith("/v1"):
        return f"{cleaned}/chat/completions"
    return f"{cleaned}/v1/chat/completions"


def _build_batch_prompt(repositories: list[Repository], custom_prompt: str | None = None) -> str:
    repo_blocks = "\n\n".join(_repository_prompt_block(repo) for repo in repositories)
    custom_section = ""
    if custom_prompt and custom_prompt.strip():
        custom_section = f"\n\n用户补充分析要求：\n{custom_prompt.strip()}"
    return (
        "请基于下面这批 GitHub Trending 仓库信息，完成一次整体分析。\n"
        "要求：\n"
        "1. 先总结这批当前流行仓库体现出的技术趋势、共同主题和可能原因；\n"
        "2. 再为每个仓库生成简体中文简介，说明它主要做什么、技术类别、为什么可能流行、实际价值；\n"
        "3. 如果用户补充分析要求存在，在不破坏 JSON 输出格式的前提下体现这些要求；\n"
        "4. 必须返回 JSON，不要 Markdown，不要代码块，格式如下：\n"
        '{"overall_summary":"...","repositories":[{"full_name":"owner/name","summary":"...","category":"...","reasons":"..."}]}\n'
        f"{custom_section}\n\n"
        "仓库列表：\n"
        f"{repo_blocks}"
    )


def _repository_prompt_block(repository: Repository) -> str:
    topics = _topics_for_prompt(repository.topics)
    readme = _truncate(repository.readme_excerpt, 700)
    detail_description = _truncate(repository.detail_description, 320)
    card_description = _truncate(repository.description, 260)
    return (
        f"仓库：{repository.owner}/{repository.name}\n"
        f"地址：{repository.url}\n"
        f"Trending 卡片描述：{card_description or '-'}\n"
        f"详情页简介：{detail_description or '-'}\n"
        f"Topics：{topics or '-'}\n"
        f"README 摘要：{readme or '-'}\n"
        f"语言：{repository.language or '-'}\n"
        f"Stars：{repository.stars if repository.stars is not None else '-'}\n"
        f"Forks：{repository.forks if repository.forks is not None else '-'}\n"
        f"Today Stars：{repository.stars_today if repository.stars_today is not None else '-'}"
    )


def _parse_batch_analysis(content: str) -> LlmBatchAnalysis:
    try:
        parsed = json.loads(_extract_json_object(content))
    except ValueError:
        return LlmBatchAnalysis(overall_summary=content)

    if not isinstance(parsed, dict):
        return LlmBatchAnalysis(overall_summary=content)

    overall_summary = _string_or_none(parsed.get("overall_summary")) or _string_or_none(parsed.get("summary")) or content
    repo_entries = parsed.get("repositories", [])
    repositories: dict[str, LlmAnalysis] = {}

    if isinstance(repo_entries, dict):
        repo_entries = [
            dict(value, full_name=key) if isinstance(value, dict) else {"full_name": key, "summary": value}
            for key, value in repo_entries.items()
        ]

    if isinstance(repo_entries, list):
        for entry in repo_entries:
            if not isinstance(entry, dict):
                continue
            full_name = _string_or_none(entry.get("full_name") or entry.get("repository") or entry.get("name"))
            summary = _string_or_none(entry.get("summary") or entry.get("introduction") or entry.get("description"))
            if not full_name or not summary:
                continue
            repositories[_repo_key(full_name)] = LlmAnalysis(
                summary=summary,
                category=_string_or_none(entry.get("category")),
                reasons=_string_or_none(entry.get("reasons") or entry.get("why_trending")),
            )

    return LlmBatchAnalysis(overall_summary=overall_summary, repositories=repositories)


def _extract_json_object(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found")
    return cleaned[start : end + 1]


def _topics_for_prompt(raw_topics: str | None) -> str | None:
    if not raw_topics:
        return None
    try:
        value = json.loads(raw_topics)
    except ValueError:
        return raw_topics
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return raw_topics


def _truncate(value: str | None, limit: int) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    return cleaned if len(cleaned) <= limit else f"{cleaned[:limit]}..."


def _string_or_none(value: object) -> str | None:
    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None
    return None


def _repo_key(full_name: str) -> str:
    return full_name.strip().lower()