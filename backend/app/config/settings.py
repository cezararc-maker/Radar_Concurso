"""Configurações centralizadas do Radar Concurso."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

APP_ENV = os.getenv("APP_ENV", "development")
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "America/Campo_Grande")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/radar_concurso.db")

NICHE_CONFIG_DIR = PROJECT_ROOT / "config" / "niches"
