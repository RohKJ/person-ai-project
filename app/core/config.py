from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample"
DB_PATH = DATA_DIR / "d2c_agent.db"

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

DEFAULT_BRAND = "LumaRoot"
DEFAULT_LOOKBACK_DAYS = 7
