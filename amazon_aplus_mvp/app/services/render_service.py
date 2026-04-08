from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from app.config import TEMPLATE_SIZES, TEMPLATES_DIR
from app.models.content import TemplateRenderPayload


class RenderService:
    def __init__(self) -> None:
        self.environment = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    def render_template_to_png(self, payload: TemplateRenderPayload, output_path: Path, global_css: str) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        template = self.environment.get_template(f"aplus/{payload.template_name}.html")
        html = template.render(**payload.data, width=payload.width, height=payload.height, global_css=global_css)

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": payload.width, "height": payload.height})
            page.set_content(html, wait_until="networkidle")
            page.screenshot(path=str(output_path), full_page=False)
            browser.close()

        return output_path

    def build_payload(self, template_name: str, data: dict) -> TemplateRenderPayload:
        size = TEMPLATE_SIZES[template_name]
        return TemplateRenderPayload(
            template_name=template_name,
            output_filename=f"{template_name}.png",
            width=size["width"],
            height=size["height"],
            data=data,
        )
