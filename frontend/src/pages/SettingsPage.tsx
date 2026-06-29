import { FormEvent, useEffect, useState } from "react";
import { ApiError, SettingsResponse, SettingsUpdate, SinceValue, getSettings, saveSettings } from "../api/client";

type Route = "/" | "/github-trending" | "/github-trending/settings";

interface SettingsPageProps {
  onNavigate: (route: Route) => void;
  onFontSizeChange: (percent: number) => void;
}

const defaults: SettingsUpdate = {
  auto_refresh_enabled: false,
  refresh_interval_minutes: 360,
  refresh_time_of_day: "09:00",
  default_since: "daily",
  default_language: null,
  max_repositories_per_refresh: 25,
  font_size_percent: 100,
  llm_base_url: null,
  llm_model: null,
  llm_timeout_seconds: 60,
  llm_custom_prompt: null,
  llm_api_key: null,
};

export default function SettingsPage({ onNavigate, onFontSizeChange }: SettingsPageProps) {
  const [form, setForm] = useState<SettingsUpdate>(defaults);
  const [loaded, setLoaded] = useState<SettingsResponse | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadSettings();
  }, []);

  async function loadSettings() {
    setLoading(true);
    setError(null);
    try {
      const settings = await getSettings();
      setLoaded(settings);
      onFontSizeChange(settings.font_size_percent);
      setForm({
        auto_refresh_enabled: settings.auto_refresh_enabled,
        refresh_interval_minutes: settings.refresh_interval_minutes,
        refresh_time_of_day: settings.refresh_time_of_day,
        default_since: settings.default_since,
        default_language: settings.default_language,
        max_repositories_per_refresh: settings.max_repositories_per_refresh,
        font_size_percent: settings.font_size_percent,
        llm_base_url: settings.llm_base_url,
        llm_model: settings.llm_model,
        llm_timeout_seconds: settings.llm_timeout_seconds,
        llm_custom_prompt: settings.llm_custom_prompt,
        llm_api_key: null,
      });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setMessage(null);
    setError(null);
    try {
      const payload: SettingsUpdate = {
        ...form,
        default_language: form.default_language?.trim() || null,
        llm_base_url: form.llm_base_url?.trim() || null,
        llm_model: form.llm_model?.trim() || null,
        llm_custom_prompt: form.llm_custom_prompt?.trim() || null,
        llm_api_key: apiKeyInput.trim() || null,
      };
      const saved = await saveSettings(payload);
      setLoaded(saved);
      setApiKeyInput("");
      onFontSizeChange(saved.font_size_percent);
      setMessage("设置已保存，定时任务已同步。");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  function updateFontSize(percent: number) {
    setForm({ ...form, font_size_percent: percent });
    onFontSizeChange(percent);
  }

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Settings</p>
          <h1>GitHub Trending 配置</h1>
          <p className="lead">管理定时刷新、抓取上限、显示字号和 OpenAI-compatible LLM 接口。</p>
        </div>
        <div className="button-row header-actions">
          <button onClick={() => onNavigate("/github-trending")}>返回列表</button>
        </div>
      </header>

      {loading && <div className="alert">加载设置中...</div>}
      {message && <div className="alert success">{message}</div>}
      {error && <div className="alert danger">{error}</div>}

      <form className="settings-form" onSubmit={handleSubmit}>
        <section className="panel form-section">
          <div className="section-head">
            <h2>刷新策略</h2>
            <span className="muted">按服务本地时间定时刷新</span>
          </div>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={form.auto_refresh_enabled}
              onChange={(event) => setForm({ ...form, auto_refresh_enabled: event.target.checked })}
            />
            <span>启用定时刷新</span>
          </label>
          <div className="form-grid">
            <label>
              <span>每日刷新时间</span>
              <input
                type="time"
                value={form.refresh_time_of_day}
                onChange={(event) => setForm({ ...form, refresh_time_of_day: event.target.value })}
              />
            </label>
            <label>
              <span>默认时间范围</span>
              <select
                value={form.default_since}
                onChange={(event) => setForm({ ...form, default_since: event.target.value as SinceValue })}
              >
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </label>
            <label>
              <span>默认编程语言</span>
              <input
                value={form.default_language ?? ""}
                onChange={(event) => setForm({ ...form, default_language: event.target.value })}
                placeholder="All languages"
              />
            </label>
            <label>
              <span>每次最多分析仓库数</span>
              <input
                type="number"
                min={1}
                max={100}
                value={form.max_repositories_per_refresh}
                onChange={(event) => setForm({ ...form, max_repositories_per_refresh: Number(event.target.value) })}
              />
            </label>
          </div>
        </section>

        <section className="panel form-section">
          <div className="section-head">
            <h2>显示</h2>
            <span className="muted">当前字号 {form.font_size_percent}%</span>
          </div>
          <label className="range-field">
            <span>整体字体大小</span>
            <input
              type="range"
              min={80}
              max={140}
              step={5}
              value={form.font_size_percent}
              onChange={(event) => updateFontSize(Number(event.target.value))}
            />
          </label>
        </section>

        <section className="panel form-section">
          <div className="section-head">
            <h2>LLM 接口</h2>
            <span className="muted">OpenAI-compatible Chat Completions</span>
          </div>
          <div className="form-grid">
            <label>
              <span>Base URL</span>
              <input
                value={form.llm_base_url ?? ""}
                onChange={(event) => setForm({ ...form, llm_base_url: event.target.value })}
                placeholder="https://api.example.com"
              />
            </label>
            <label>
              <span>Model</span>
              <input
                value={form.llm_model ?? ""}
                onChange={(event) => setForm({ ...form, llm_model: event.target.value })}
                placeholder="gpt-4.1-mini / deepseek-chat"
              />
            </label>
            <label>
              <span>API Key</span>
              <input
                type="password"
                value={apiKeyInput}
                onChange={(event) => setApiKeyInput(event.target.value)}
                placeholder={loaded?.has_llm_api_key ? "已保存，留空则不修改" : "请输入 API Key"}
              />
            </label>
            <label>
              <span>请求超时（秒）</span>
              <input
                type="number"
                min={5}
                max={300}
                value={form.llm_timeout_seconds}
                onChange={(event) => setForm({ ...form, llm_timeout_seconds: Number(event.target.value) })}
              />
            </label>
          </div>
          <label>
            <span>AI 提示词补充</span>
            <textarea
              value={form.llm_custom_prompt ?? ""}
              onChange={(event) => setForm({ ...form, llm_custom_prompt: event.target.value })}
              placeholder="例如：重点关注商业化价值、国内团队可落地性、开源协议风险等。"
              rows={6}
            />
          </label>
        </section>

        <div className="button-row sticky-actions">
          <button type="button" onClick={() => onNavigate("/github-trending")}>取消</button>
          <button className="primary" type="submit" disabled={saving}>{saving ? "保存中..." : "保存设置"}</button>
        </div>
      </form>
    </section>
  );
}

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "未知错误";
}