import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

print(f"[config] ENV_PATH: {ENV_PATH}")
print(f"[config] .env exists: {ENV_PATH.exists()}")

# Extra explicit env debug requested by user.
print("ENV TEST")
print("API KEY:", os.getenv("OPENAI_API_KEY"))

APP_DIR = BASE_DIR / "app"
STATIC_DIR = APP_DIR / "static"
TEMPLATES_DIR = APP_DIR / "templates"
EXPORTS_DIR = STATIC_DIR / "exports"
UPLOADS_DIR = STATIC_DIR / "uploads"
SAMPLE_DATA_PATH = APP_DIR / "sample_data" / "sample_product.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

print(f"[config] OPENAI_API_KEY loaded: {bool(OPENAI_API_KEY)}")

MARKETPLACES = ["DE", "FR", "NL", "IT", "ES"]

# Central place for Amazon A+ image sizes per module.
TEMPLATE_SIZES = {
    "hero": {"width": 1464, "height": 600},
    "body_mapping": {"width": 1464, "height": 600},
    "problem_solution": {"width": 1464, "height": 600},
    "features": {"width": 1464, "height": 600},
    "compatibility": {"width": 1464, "height": 600},
}

TEMPLATE_ORDER = [
    "hero",
    "body_mapping",
    "problem_solution",
    "features",
    "compatibility",
]
