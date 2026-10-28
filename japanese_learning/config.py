from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODEL_ID = "Qwen/Qwen3.5-9B"
MODEL_REVISION = "c202236235762e1c871ad0ccb60c8ee5ba337b9a"
MODEL_DIR = ROOT / "models" / "Qwen3.5-9B"
PROMPT_VERSION = "8"
DB_PATH = ROOT / "data" / "practice.sqlite3"
