import json

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import MARKETPLACES, SAMPLE_DATA_PATH, TEMPLATES_DIR
from app.models.content import MasterCopyInput
from app.services.ai_service import AIContentService
from app.services.export_service import ExportService
from app.services.product_service import ProductService

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _parse_lines(raw: str) -> list[str]:
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


def _build_master_copy_from_form(
    hero_headline: str,
    hero_subtext: str,
    benefit_titles: list[str],
    benefit_texts: list[str],
    problem_title: str,
    problem_text: str,
    solution_title: str,
    solution_text: str,
    compatibility_points_text: str,
    use_case_points_text: str,
    module_text_hero: str,
    module_text_body_mapping: str,
    module_text_problem_solution: str,
    module_text_features: str,
    module_text_compatibility: str,
) -> MasterCopyInput:
    benefit_blocks = []
    for idx in range(4):
        title = benefit_titles[idx] if idx < len(benefit_titles) else ""
        text = benefit_texts[idx] if idx < len(benefit_texts) else ""
        benefit_blocks.append({"title": title, "text": text})

    return MasterCopyInput.model_validate(
        {
            "hero_headline": hero_headline,
            "hero_subtext": hero_subtext,
            "benefit_blocks": benefit_blocks,
            "problem_title": problem_title,
            "problem_text": problem_text,
            "solution_title": solution_title,
            "solution_text": solution_text,
            "compatibility_points": _parse_lines(compatibility_points_text),
            "use_case_points": _parse_lines(use_case_points_text),
            "module_texts": {
                "hero": module_text_hero,
                "body_mapping": module_text_body_mapping,
                "problem_solution": module_text_problem_solution,
                "features": module_text_features,
                "compatibility": module_text_compatibility,
            },
        }
    )


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    sample_json = SAMPLE_DATA_PATH.read_text(encoding="utf-8") if SAMPLE_DATA_PATH.exists() else "{}"
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "marketplaces": MARKETPLACES,
            "sample_json": sample_json,
            "master_copy_json": "",
            "error": None,
            "result": None,
        },
    )


@router.post("/generate", response_class=HTMLResponse)
def generate(
    request: Request,
    product_json: str = Form(""),
    master_copy_json: str = Form(""),
    selected_marketplaces: list[str] = Form(default=[]),
) -> HTMLResponse:
    product_json = (product_json or "").strip()
    master_copy_json = (master_copy_json or "").strip()
    selected_marketplaces = [m.strip().upper() for m in selected_marketplaces if m and m.strip()]

    if not product_json:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "marketplaces": MARKETPLACES,
                "sample_json": "",
                "master_copy_json": master_copy_json,
                "error": "Product JSON mag niet leeg zijn.",
                "result": None,
            },
        )

    if not selected_marketplaces:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "marketplaces": MARKETPLACES,
                "sample_json": product_json,
                "master_copy_json": master_copy_json,
                "error": "Selecteer minstens 1 marketplace.",
                "result": None,
            },
        )

    try:
        product = ProductService.parse_product_json(product_json)

        allowed = set(product.allowed_marketplaces)
        marketplaces = [m for m in selected_marketplaces if m in allowed]
        if not marketplaces:
            raise ValueError("Geen geldige marketplaces gekozen op basis van allowed_marketplaces.")

        if master_copy_json:
            master_copy = ProductService.parse_master_copy_json(master_copy_json)
            master_copy_source = "provided"
        else:
            master_base_market = marketplaces[0] if marketplaces else "NL"
            generated = AIContentService().generate_marketplace_copy(product, master_base_market)
            master_copy = MasterCopyInput.model_validate(generated.model_dump())
            master_copy_source = "generated"

        return templates.TemplateResponse(
            request=request,
            name="edit.html",
            context={
                "product": product,
                "product_json": product_json,
                "selected_marketplaces": marketplaces,
                "selected_marketplaces_csv": ",".join(marketplaces),
                "master_copy": master_copy,
                "master_copy_source": master_copy_source,
                "error": None,
            },
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "marketplaces": MARKETPLACES,
                "sample_json": product_json,
                "master_copy_json": master_copy_json,
                "error": str(exc),
                "result": None,
            },
        )


@router.post("/edit", response_class=HTMLResponse)
def edit_alias(
    request: Request,
    product_json: str = Form(""),
    master_copy_json: str = Form(""),
    selected_marketplaces: list[str] = Form(default=[]),
) -> HTMLResponse:
    # Alias to support explicit 2-step route naming in the UI.
    return generate(
        request=request,
        product_json=product_json,
        master_copy_json=master_copy_json,
        selected_marketplaces=selected_marketplaces,
    )


@router.post("/generate-marketplaces", response_class=HTMLResponse)
def generate_marketplaces(
    request: Request,
    product_json: str = Form(""),
    selected_marketplaces_csv: str = Form(""),
    hero_headline: str = Form(""),
    hero_subtext: str = Form(""),
    benefit_titles: list[str] = Form(default=[]),
    benefit_texts: list[str] = Form(default=[]),
    problem_title: str = Form(""),
    problem_text: str = Form(""),
    solution_title: str = Form(""),
    solution_text: str = Form(""),
    compatibility_points_text: str = Form(""),
    use_case_points_text: str = Form(""),
    module_text_hero: str = Form(""),
    module_text_body_mapping: str = Form(""),
    module_text_problem_solution: str = Form(""),
    module_text_features: str = Form(""),
    module_text_compatibility: str = Form(""),
) -> HTMLResponse:
    try:
        product = ProductService.parse_product_json((product_json or "").strip())
        marketplaces = [m.strip().upper() for m in selected_marketplaces_csv.split(",") if m.strip()]
        if not marketplaces:
            raise ValueError("Selecteer minstens 1 marketplace.")

        master_copy = _build_master_copy_from_form(
            hero_headline=hero_headline,
            hero_subtext=hero_subtext,
            benefit_titles=benefit_titles,
            benefit_texts=benefit_texts,
            problem_title=problem_title,
            problem_text=problem_text,
            solution_title=solution_title,
            solution_text=solution_text,
            compatibility_points_text=compatibility_points_text,
            use_case_points_text=use_case_points_text,
            module_text_hero=module_text_hero,
            module_text_body_mapping=module_text_body_mapping,
            module_text_problem_solution=module_text_problem_solution,
            module_text_features=module_text_features,
            module_text_compatibility=module_text_compatibility,
        )

        result = ExportService().generate_exports(
            product=product,
            marketplaces=marketplaces,
            master_copy=master_copy,
            render_images=False,
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "result": result,
                "product": product,
                "selected_marketplaces": marketplaces,
                "generation_mode": "rewrite",
                "mode_message": "Edited master copy used: marketplace rewrite mode applied",
                "raw_product": json.dumps(product.model_dump(), indent=2, ensure_ascii=False),
            },
        )
    except Exception as exc:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "marketplaces": MARKETPLACES,
                "sample_json": product_json,
                "master_copy_json": "",
                "error": str(exc),
                "result": None,
            },
        )
