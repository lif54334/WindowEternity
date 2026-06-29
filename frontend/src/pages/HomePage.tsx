type Route = "/" | "/github-trending" | "/github-trending/settings";

interface HomePageProps {
  onNavigate: (route: Route) => void;
}

export default function HomePage({ onNavigate }: HomePageProps) {
  return (
    <section className="page-stack">
      <header className="page-header portal-header">
        <div>
          <p className="eyebrow">Project portal</p>
          <h1>Window of Eternity</h1>
          <p className="lead">新世界的窗口，用一个本地入口组织未来的功能模块。</p>
        </div>
        <div className="status-tile">
          <span className="status-dot ready" />
          <span>Local module hub</span>
        </div>
      </header>

      <section className="module-grid" aria-label="Feature modules">
        <article className="module-card">
          <div className="module-card-head">
            <span className="module-icon">GH</span>
            <span className="pill">MVP</span>
          </div>
          <h2>GitHub Trending 抓取</h2>
          <p>抓取 GitHub 当前趋势库，展示基础信息、统计分布，并通过大模型生成中文技术分析。</p>
          <dl className="module-facts">
            <div><dt>刷新</dt><dd>定时 + 手动</dd></div>
            <div><dt>范围</dt><dd>daily / weekly / monthly</dd></div>
            <div><dt>分析</dt><dd>每次刷新全量重跑</dd></div>
          </dl>
          <div className="button-row">
            <button className="primary" onClick={() => onNavigate("/github-trending")}>打开模块</button>
            <button onClick={() => onNavigate("/github-trending/settings")}>配置</button>
          </div>
        </article>
      </section>
    </section>
  );
}
