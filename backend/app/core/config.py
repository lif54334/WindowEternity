from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BASE_DIR.parent
DATA_DIR = Path(os.getenv("WINDOW_ETERNITY_DATA_DIR", str(REPO_ROOT / "data"))).resolve()
DATABASE_URL = os.getenv("WINDOW_ETERNITY_DATABASE_URL", f"sqlite:///{(DATA_DIR / 'window_eternity.db').as_posix()}")
FRONTEND_DIST = Path(os.getenv("WINDOW_ETERNITY_FRONTEND_DIST", str(REPO_ROOT / "frontend" / "dist"))).resolve()
APP_HOST = os.getenv("WINDOW_ETERNITY_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("WINDOW_ETERNITY_PORT", "3030"))
GITHUB_TRENDING_BASE_URL = "https://github.com/trending"
DEFAULT_USER_AGENT = "WindowOfEternity/0.1 (+https://github.com/trending)"


