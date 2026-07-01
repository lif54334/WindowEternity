import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  RefreshRunResponse,
  RepositoryResponse,
  SinceValue,
  TrendingResponse,
  TrendingStatsResponse,
  analyzeTrending,
  getRefreshHistory,
  getTrending,
  getTrendingStats,
  refreshTrending,
} from "../api/client";

type Route = "/" | "/github-trending" | "/github-trending/settings";

interface GitHubTrendingPageProps {
  onNavigate: (route: Route) => void;
}

const sinceOptions: Array<{ value: SinceValue; label: string }> = [
  { value: "daily", label: "Daily" },
  { value: "weekly", label: "Weekly" },
  { value: "monthly", label: "Monthly" },
];

export default function GitHubTrendingPage({ onNavigate }: GitHubTrendingPageProps) {
  const [since, setSince] = useState<SinceValue>("daily");
  const [language, setLanguage] = useState("");
  const [trending, setTrending] = useState<TrendingResponse | null>(null);
  const [stats, setStats] = useState<TrendingStatsResponse | null>(null);
  const [history, setHistory] = useState<RefreshRunResponse[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [busyAction, setBusyAction] = useState<"refresh" | "analyze" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const repositories = trending?.repositories ?? [];
  const latestRun = trending?.latest_run ?? null;
  const showHistory = history.length > 0;

  useEffect(() => {
    void loadData();
  }, []);

  const languageLabel = useMemo(() => language.trim() || "All languages", [language]);

  async function loadData(nextSince = since, nextLanguage = language, nextRunId = selectedRunId) {
    setLoading(true);
    setError(null);
    try {
      const [trendingData, statsData, historyData] = await Promise.all([
        getTrending(nextSince, nextLanguage, nextRunId ?? undefined),
        getTrendingStats(nextSince, nextLanguage, nextRunId ?? undefined),
        getRefreshHistory(),
      ]);
      setTrending(trendingData);
      setStats(statsData);
      setHistory(historyData.runs);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function reloadHistory() {
    const historyData = await getRefreshHistory();
    setHistory(historyData.runs);
  }

  async function handleApplyFilters() {
    setSelectedRunId(null);
    await loadData(since, language, null);
  }

  async function handleHistorySelect(run: RefreshRunResponse) {
    const runSince = isSinceValue(run.since) ? run.since : since;
    const runLanguage = run.language ?? "";
    setSelectedRunId(run.id);
    setSince(runSince);
    setLanguage(runLanguage);
    await loadData(runSince, runLanguage, run.id);
  }

  async function handleRefresh() {
    setBusyAction("refresh");
    setError(null);
    try {
      setSelectedRunId(null);
      const data = await refreshTrending(since, language);
      setTrending(data);
      setStats(await getTrendingStats(since, language));
      await reloadHistory();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyAction(null);
    }
  }

  async function handleAnalyze() {
    setBusyAction("analyze");
    setError(null);
    try {
      setSelectedRunId(null);
      const data = await analyzeTrending(since, language);
      setTrending(data);
      setStats(await getTrendingStats(since, language));
      await reloadHistory();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <section className={`trending-workspace ${showHistory ? "with-history" : "no-history"}`}>
      {showHistory && <HistoryRail runs={history} activeRunId={latestRun?.id ?? null} onSelect={handleHistorySelect} />}

      <div className="page-stack">
        <header className="page-header">
          <div>
            <p className="eyebrow">GitHub Trending</p>
            <h1>流行仓库监测</h1>
            <p className="lead">抓取趋势仓库和详情页信息，并把本次流行仓库统一交给 LLM 生成简介与趋势总结。</p>
          </div>
          <div className="button-row header-actions">
            <button onClick={() => onNavigate("/github-trending/settings")}>设置</button>
            <button className="primary" onClick={handleRefresh} disabled={busyAction !== null}>
              {busyAction === "refresh" ? "刷新中..." : "手动刷新"}
            </button>
          </div>
        </header>

        <section className="toolbar" aria-label="Trending filters">
          <label>
            <span>时间范围</span>
            <select value={since} onChange={(event) => setSince(event.target.value as SinceValue)}>
              {sinceOptions.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>编程语言</span>
            <input value={language} onChange={(event) => setLanguage(event.target.value)} placeholder="All languages" />
          </label>
          <button onClick={handleApplyFilters} disabled={loading}>应用筛选</button>
          <button onClick={handleAnalyze} disabled={busyAction !== null || repositories.length === 0}>
            {busyAction === "analyze" ? "分析中..." : "重新分析当前列表"}
          </button>
        </section>

        {error && <div className="alert danger">{error}</div>}
        {latestRun?.error_message && <div className="alert warning">最近刷新提示：{latestRun.error_message}</div>}
        {latestRun?.ai_summary_error && <div className="alert warning">AI 总结提示：{latestRun.ai_summary_error}</div>}

        <section className="metric-grid" aria-label="Statistics">
          <Metric label="仓库数" value={String(stats?.repository_count ?? repositories.length)} />
          <Metric label="筛选范围" value={`${since} / ${languageLabel}`} />
          <Metric label="最近状态" value={latestRun?.status ?? "未刷新"} />
          <Metric label="分析时间" value={formatDateTime(latestRun?.finished_at ?? latestRun?.started_at)} />
        </section>

        {latestRun?.ai_summary && (
          <section className="panel ai-summary-panel">
            <div className="section-head">
              <div>
                <h2>本次流行仓库 AI 总结</h2>
                <span className="muted">分析时间：{formatDateTime(latestRun.finished_at ?? latestRun.started_at)}</span>
              </div>
              <span className={`analysis-badge ${latestRun.ai_summary_status ?? "pending"}`}>{latestRun.ai_summary_status}</span>
            </div>
            <div className="analysis-box summary-box">{latestRun.ai_summary}</div>
          </section>
        )}

        <section className="split-layout">
          <div className="panel">
            <div className="section-head">
              <h2>当前趋势列表</h2>
              {loading && <span className="muted">加载中...</span>}
            </div>
            <div className="repo-list">
              {repositories.length === 0 && <p className="empty-state">暂无数据。请先手动刷新，或在设置中开启定时刷新。</p>}
              {repositories.map((repo) => <RepositoryItem key={repo.id} repo={repo} />)}
            </div>
          </div>
          <aside className="panel stats-panel">
            <h2>统计分析</h2>
            <h3>语言分布</h3>
            <StatBars data={stats?.language_distribution.map((item) => ({ label: item.language, count: item.count })) ?? []} />
          </aside>
        </section>
      </div>

      {busyAction === "refresh" && (
        <div className="refresh-overlay" role="status" aria-live="polite">
          <div className="refresh-dialog">
            <div className="spinner" aria-hidden="true" />
            <h2>正在刷新 GitHub Trending</h2>
            <p>正在抓取趋势列表、补充仓库详情，并在配置可用时进行 AI 分析。</p>
            <div className="progress-dots" aria-hidden="true"><span /><span /><span /></div>
          </div>
        </div>
      )}
    </section>
  );
}

function HistoryRail({
  runs,
  activeRunId,
  onSelect,
}: {
  runs: RefreshRunResponse[];
  activeRunId: number | null;
  onSelect: (run: RefreshRunResponse) => void;
}) {
  return (
    <aside className="history-rail" aria-label="Refresh history">
      <div className="history-rail-head">
        <h2>分析历史</h2>
        <span>{runs.length}</span>
      </div>
      <div className="history-list">
        {runs.map((run) => (
          <button
            type="button"
            className={"history-item " + (run.id === activeRunId ? "active" : "")}
            key={run.id}
            onClick={() => onSelect(run)}
            aria-current={run.id === activeRunId ? "true" : undefined}
          >
            <div className="history-item-top">
              <strong>#{run.id}</strong>
              <span className={"analysis-badge " + (run.ai_summary_status ?? run.status)}>{run.ai_summary_status ?? run.status}</span>
            </div>
            <div className="history-time">{formatDateTime(run.finished_at ?? run.started_at)}</div>
            <div className="history-meta">{run.since} / {run.language || "All languages"}</div>
            {run.ai_summary && <p>{run.ai_summary}</p>}
            {run.error_message && <p className="history-error">{run.error_message}</p>}
          </button>
        ))}
      </div>
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RepositoryItem({ repo }: { repo: RepositoryResponse }) {
  const analysisStatus = repo.analysis?.status ?? "pending";
  const detailDescription = repo.detail_description && repo.detail_description !== repo.description ? repo.detail_description : null;
  return (
    <article className="repo-item">
      <div className="repo-rank">#{repo.rank}</div>
      <div className="repo-content">
        <div className="repo-title-row">
          <a href={repo.url} target="_blank" rel="noreferrer">{repo.owner}/{repo.name}</a>
          <span className={`analysis-badge ${analysisStatus}`}>{analysisStatus}</span>
        </div>
        <p className="repo-description">{repo.description || "No description provided on Trending."}</p>
        {detailDescription && <p className="repo-detail-description">详情页：{detailDescription}</p>}
        {repo.topics.length > 0 && (
          <div className="topic-row" aria-label="Repository topics">
            {repo.topics.map((topic) => <span key={topic}>{topic}</span>)}
          </div>
        )}
        <div className="repo-meta">
          <span>{repo.language || "Unknown"}</span>
          <span>{formatNumber(repo.stars)} stars</span>
          <span>{formatNumber(repo.forks)} forks</span>
          <span>{formatNumber(repo.stars_today)} today</span>
        </div>
        {repo.analysis?.summary && (
          <div className="analysis-box">
            <strong>AI 简介</strong>
            <span className="analysis-time">生成时间：{formatDateTime(repo.analysis.created_at)}</span>
            <div>{repo.analysis.summary}</div>
          </div>
        )}
        {repo.readme_excerpt && (
          <details className="readme-excerpt">
            <summary>仓库 README 摘要</summary>
            <p>{repo.readme_excerpt}</p>
          </details>
        )}
        {repo.analysis?.error_message && <div className="alert warning compact">{repo.analysis.error_message}</div>}
      </div>
    </article>
  );
}

function StatBars({ data }: { data: Array<{ label: string; count: number }> }) {
  if (data.length === 0) return <p className="empty-state small">暂无统计数据</p>;
  const max = Math.max(...data.map((item) => item.count), 1);
  return (
    <div className="stat-bars">
      {data.map((item) => (
        <div className="stat-row" key={item.label}>
          <span>{item.label}</span>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${(item.count / max) * 100}%` }} /></div>
          <strong>{item.count}</strong>
        </div>
      ))}
    </div>
  );
}

function formatNumber(value: number | null): string {
  return value == null ? "-" : value.toLocaleString();
}

const eastEightDateTimeFormatter = new Intl.DateTimeFormat("zh-CN", {
  timeZone: "Asia/Shanghai",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

function formatDateTime(value: string | null | undefined): string {
  if (!value) return "-";
  const trimmed = value.trim();
  const hasTimeZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(trimmed);
  const date = new Date(hasTimeZone ? trimmed : trimmed + "Z");
  if (Number.isNaN(date.getTime())) return value;
  return eastEightDateTimeFormatter.format(date);
}

function isSinceValue(value: string): value is SinceValue {
  return value === "daily" || value === "weekly" || value === "monthly";
}

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "未知错误";
}