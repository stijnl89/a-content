from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import EXPORTS_DIR, STATIC_DIR, UPLOADS_DIR
from app.routes.api import router as api_router
from app.routes.pages import router as pages_router
from app.utils.file_helpers import ensure_dir

app = FastAPI(title="Amazon A+ MVP Generator", version="0.1.0")

ensure_dir(UPLOADS_DIR)
ensure_dir(EXPORTS_DIR)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(pages_router)
app.include_router(api_router)
