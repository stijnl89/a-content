from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.models.content import ExportResult, MasterCopyInput
from app.models.product import ProductInput
from app.services.export_service import ExportService

router = APIRouter(prefix="/api", tags=["api"])


class GenerateRequest(BaseModel):
    product: ProductInput
    marketplaces: list[str] = Field(default_factory=list)
    master_copy: MasterCopyInput | None = None


@router.post("/generate", response_model=ExportResult)
def api_generate(payload: GenerateRequest) -> ExportResult:
    marketplaces = payload.marketplaces or payload.product.allowed_marketplaces
    return ExportService().generate_exports(
        product=payload.product,
        marketplaces=marketplaces,
        master_copy=payload.master_copy,
        render_images=False,
    )
