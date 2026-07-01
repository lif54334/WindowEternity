import { useEffect, useState } from "react";
import { getSettings } from "./api/client";
import HomePage from "./pages/HomePage";
import GitHubTrendingPage from "./pages/GitHubTrendingPage";
import MarketPricesPage from "./pages/MarketPricesPage";
import SettingsPage from "./pages/SettingsPage";

type Route = "/" | "/github-trending" | "/github-trending/settings" | "/market-prices";

const routes: Route[] = ["/", "/github-trending", "/github-trending/settings", "/market-prices"];

function normalizeRoute(pathname: string): Route {
  return routes.includes(pathname as Route) ? (pathname as Route) : "/";
}

export function applyFontSize(percent: number): void {
  const bounded = Math.min(Math.max(percent, 80), 140);
  document.documentElement.style.setProperty("--app-font-scale", String(bounded / 100));
}

export default function App() {
  const [route, setRoute] = useState<Route>(() => normalizeRoute(window.location.pathname));

  useEffect(() => {
    const onPopState = () => setRoute(normalizeRoute(window.location.pathname));
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    void getSettings()
      .then((settings) => applyFontSize(settings.font_size_percent))
      .catch(() => applyFontSize(100));
  }, []);

  const navigate = (nextRoute: Route) => {
    window.history.pushState({}, "", nextRoute);
    setRoute(nextRoute);
  };

  if (route === "/") {
    return (
      <main className="portal-main">
        <HomePage onNavigate={navigate} />
      </main>
    );
  }

  return (
    <div className="feature-shell">
      <header className="feature-topbar">
        <button className="brand" onClick={() => navigate("/")}> 
          <span className="brand-mark">WE</span>
          <span>
            <strong>Window of Eternity</strong>
            <small>新世界的窗口</small>
          </span>
        </button>
      </header>
      <main className="feature-main">
        {route === "/github-trending" && <GitHubTrendingPage onNavigate={navigate} />}
        {route === "/github-trending/settings" && <SettingsPage onNavigate={navigate} onFontSizeChange={applyFontSize} />}
        {route === "/market-prices" && <MarketPricesPage onNavigate={navigate} />}
      </main>
    </div>
  );
}
