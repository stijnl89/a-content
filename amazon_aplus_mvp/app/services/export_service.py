import json
from typing import Optional

from app.config import EXPORTS_DIR, TEMPLATE_ORDER
from app.models.content import ExportResult, MarketplaceExport, MasterCopyInput
from app.models.product import ProductInput
from app.services.ai_service import AIContentService
from app.utils.file_helpers import ensure_dir
from app.utils.slugify import slugify


class ExportService:
    def __init__(self) -> None:
        self.ai_service = AIContentService()

    def generate_exports(
        self,
        product: ProductInput,
        marketplaces: list[str],
        master_copy: Optional[MasterCopyInput] = None,
        render_images: bool = False,
        global_css: Optional[str] = None,
    ) -> ExportResult:
        product_slug = slugify(f"{product.brand_name}-{product.product_name}")
        product_export_dir = ensure_dir(EXPORTS_DIR / product_slug)

        marketplace_exports: list[MarketplaceExport] = []

        for marketplace in marketplaces:
            market_dir = ensure_dir(product_export_dir / marketplace)

            if master_copy:
                content = self.ai_service.rewrite_marketplace_copy(master_copy, product, marketplace)
            else:
                content = self.ai_service.generate_marketplace_copy(product, marketplace)

            content = self.ai_service.validate_claims(content, product.forbidden_claims)

            image_paths: list[str] = []
            preview_urls: list[str] = []

            if render_images:
                if not global_css:
                    raise ValueError("global_css is required when render_images=True")

                from app.services.render_service import RenderService

                render_service = RenderService()
                for template_name in TEMPLATE_ORDER:
                    template_data = {
                        "product": product.model_dump(),
                        "content": content.model_dump(),
                        "marketplace": marketplace,
                    }
                    payload = render_service.build_payload(template_name, template_data)
                    output_path = market_dir / payload.output_filename
                    render_service.render_template_to_png(payload, output_path, global_css=global_css)

                    image_paths.append(str(output_path))
                    relative_path = output_path.relative_to(EXPORTS_DIR.parent)
                    preview_urls.append("/" + str(relative_path).replace("\\", "/"))
            else:
                # Placeholder output references so UI can show what will be rendered later.
                preview_urls = [f"placeholder:{template_name}" for template_name in TEMPLATE_ORDER]

            copy_path = market_dir / "copy.json"
            copy_path.write_text(
                json.dumps(content.model_dump(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            copy_relative = copy_path.relative_to(EXPORTS_DIR.parent)
            copy_url = "/" + str(copy_relative).replace("\\", "/")

            marketplace_exports.append(
                MarketplaceExport(
                    marketplace=marketplace,
                    copy_path=str(copy_path),
                    copy_url=copy_url,
                    copy_content=content.model_dump(),
                    image_paths=image_paths,
                    preview_urls=preview_urls,
                )
            )

        return ExportResult(
            product_slug=product_slug,
            exports_dir=str(product_export_dir),
            marketplaces=marketplace_exports,
        )
