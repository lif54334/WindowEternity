import { useEffect, useState } from "react";
import { ApiError, MarketPricesResponse, MetalPriceResponse, getMarketPrices } from "../api/client";

type Route = "/" | "/github-trending" | "/github-trending/settings" | "/market-prices";

interface MarketPricesPageProps {
  onNavigate: (route: Route) => void;
}

export default function MarketPricesPage({ onNavigate }: MarketPricesPageProps) {
  const [data, setData] = useState<MarketPricesResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadPrices();
  }, []);

  async function loadPrices() {
    setLoading(true);
    setError(null);
    try {
      setData(await getMarketPrices());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Market Prices</p>
          <h1>国际金银价格</h1>
          <p className="lead">实时读取国际黄金、国际白银美元报价，并按 USD/CNY 汇率换算成人民币价格。</p>
        </div>
        <div className="button-row header-actions">
          <button onClick={() => onNavigate("/")}>返回主页</button>
          <button className="primary" onClick={loadPrices} disabled={loading}>
            {loading ? "刷新中..." : "手动刷新"}
          </button>
        </div>
      </header>

      {error && <div className="alert danger">{error}</div>}

      <section className="metric-grid market-summary" aria-label="Market price source">
        <div className="metric">
          <span>汇率来源</span>
          <strong>{data?.exchange_rate_symbol ?? "CNY=X"}</strong>
        </div>
        <div className="metric">
          <span>USD/CNY</span>
          <strong>{formatDecimal(data?.exchange_rate, 4)}</strong>
        </div>
        <div className="metric">
          <span>汇率时间</span>
          <strong>{formatDateTime(data?.exchange_rate_time)}</strong>
        </div>
        <div className="metric">
          <span>后端抓取</span>
          <strong>{formatDateTime(data?.fetched_at)}</strong>
        </div>
      </section>

      <section className="price-grid" aria-label="Precious metal prices">
        {loading && !data && <p className="empty-state">正在加载当前金银价格...</p>}
        {!loading && !data && !error && <p className="empty-state">暂无价格数据，请手动刷新。</p>}
        {data?.prices.map((price) => <PriceCard key={price.metal} price={price} />)}
      </section>

      <section className="panel">
        <h2>数据说明</h2>
        <p className="muted">
          当前模块使用 Yahoo Finance chart endpoint 读取 COMEX 黄金、白银合约报价和 USD/CNY 汇率。
          人民币价格按“美元/金衡盎司 x USD/CNY”计算，同时换算为“人民币/克”便于阅读。
        </p>
      </section>
    </section>
  );
}

function PriceCard({ price }: { price: MetalPriceResponse }) {
  return (
    <article className="panel price-card">
      <div className="price-card-head">
        <div>
          <p className="eyebrow">{price.source_symbol}</p>
          <h2>{price.display_name}</h2>
        </div>
        <span className="pill">{price.source_name}</span>
      </div>
      <div className="price-primary">
        <span>人民币/金衡盎司</span>
        <strong>{formatCurrency(price.price_cny_per_ounce)}</strong>
      </div>
      <div className="price-secondary-grid">
        <Metric label="人民币/克" value={formatCurrency(price.price_cny_per_gram)} />
        <Metric label="美元/金衡盎司" value={`$${formatDecimal(price.price_usd_per_ounce, 2)}`} />
        <Metric label="USD/CNY" value={formatDecimal(price.usd_cny_rate, 4)} />
        <Metric label="报价时间" value={formatDateTime(price.quote_time)} />
      </div>
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="compact-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
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

function formatCurrency(value: number | null | undefined): string {
  if (value == null) return "-";
  return `¥${value.toLocaleString("zh-CN", { maximumFractionDigits: 2, minimumFractionDigits: 2 })}`;
}

function formatDecimal(value: number | null | undefined, digits: number): string {
  if (value == null) return "-";
  return value.toLocaleString("zh-CN", { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "未知错误";
}
