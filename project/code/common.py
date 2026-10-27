"""Semua path dan konstanta Project 10. ROOT = folder project/."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "data" / "raw"          # data simulasi dari generator (di-commit)
CLEAN_DIR = ROOT / "data" / "clean"      # hasil cleaning (tidak di-commit)
GT_DIR = ROOT / "data"                   # ground truth (di-commit)
DB_PATH = ROOT / "cycletime.duckdb"      # file database (tidak di-commit, dibuat ulang)

SQL_PREP = ROOT / "code" / "1-data-preparation" / "sql"
SQL_ANALYSIS = ROOT / "code" / "2-analysis" / "sql"
RES_PREP = ROOT / "results" / "1-data-preparation"
RES_ANALYSIS = ROOT / "results" / "2-analysis"
RES_PRESENT = ROOT / "results" / "3-presentation"
DOCS_DIR = ROOT / "docs"

# Parameter simulasi (seed tetap, sehingga data selalu sama)
SEED = 20260302
START_DATE = "2026-03-02"
N_WORKDAYS = 60
HOURS_NORMAL = 8
HOURS_OVERTIME = 10
MAX_HOURS_VALID = 12                     # jam kerja di atas ini dianggap tidak wajar
MIN_DAYS_OPERATOR = 5                    # operator dengan data kurang dari ini tidak dibandingkan
MODELS = ["2-layer", "4-layer", "8-layer"]

for d in (RAW_DIR, CLEAN_DIR, RES_PREP, RES_ANALYSIS, RES_PRESENT):
    d.mkdir(parents=True, exist_ok=True)
