from typing import Any

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _short_overlay_text(headline: str, max_words: int = 6, max_chars: int = 60) -> str:
    clean = " ".join((headline or "").split())
    if not clean:
        return ""

    words = clean.split(" ")
    short = " ".join(words[:max_words])
    if len(short) > max_chars:
        short = short[: max_chars - 1].rstrip() + "..."
    return short


def _benefits_subtext(benefits: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for block in benefits[:3]:
        title = str(block.get("title", "")).strip()
        text = str(block.get("text", "")).strip()
        if title and text:
            parts.append(f"{title}: {text}")
        elif title:
            parts.append(title)
        elif text:
            parts.append(text)
    return " | ".join(parts)


def generate_asset_briefs_from_structured_copy(data: dict[str, Any]) -> list[dict[str, str]]:
    hero_headline = str(data.get("hero_headline", "")).strip()
    hero_subtext = str(data.get("hero_subtext", "")).strip()

    benefit_blocks = data.get("benefit_blocks", [])
    if not isinstance(benefit_blocks, list):
        benefit_blocks = []

    problem_title = str(data.get("problem_title", "")).strip()
    problem_text = str(data.get("problem_text", "")).strip()
    solution_title = str(data.get("solution_title", "")).strip()
    solution_text = str(data.get("solution_text", "")).strip()

    use_case_points = data.get("use_case_points", [])
    if not isinstance(use_case_points, list):
        use_case_points = []

    compatibility_points = data.get("compatibility_points", [])
    if not isinstance(compatibility_points, list):
        compatibility_points = []

    use_case_subtext = " | ".join([str(item).strip() for item in use_case_points if str(item).strip()])
    compatibility_subtext = " | ".join([str(item).strip() for item in compatibility_points if str(item).strip()])

    problem_solution_headline = " / ".join([part for part in [problem_title, solution_title] if part])
    problem_solution_subtext = " | ".join([part for part in [problem_text, solution_text] if part])

    modules: list[dict[str, str]] = [
        {
            "module_type": "HERO",
            "headline": hero_headline,
            "subtext": hero_subtext,
            "layout": "centered",
            "image_idea": "clean product shot or lifestyle use",
            "overlay_text": _short_overlay_text(hero_headline),
        },
        {
            "module_type": "BENEFITS",
            "headline": "Key Benefits",
            "subtext": _benefits_subtext(benefit_blocks),
            "layout": "3_column",
            "image_idea": "icons or small visuals per benefit",
            "overlay_text": _short_overlay_text("Key Benefits"),
        },
        {
            "module_type": "PROBLEM_SOLUTION",
            "headline": problem_solution_headline,
            "subtext": problem_solution_subtext,
            "layout": "split",
            "image_idea": "before/after or pain vs relief",
            "overlay_text": _short_overlay_text(problem_solution_headline),
        },
        {
            "module_type": "USE_CASE",
            "headline": "Use Cases",
            "subtext": use_case_subtext,
            "layout": "grid",
            "image_idea": "real life scenarios",
            "overlay_text": _short_overlay_text("Use Cases"),
        },
        {
            "module_type": "COMPATIBILITY",
            "headline": "Compatibility",
            "subtext": compatibility_subtext,
            "layout": "list",
            "image_idea": "device connections or compatibility icons",
            "overlay_text": _short_overlay_text("Compatibility"),
        },
    ]

    return modules


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = (text or "").split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]

    for word in words[1:]:
        candidate = f"{current} {word}"
        bbox = draw.textbbox((0, 0), candidate, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word

    lines.append(current)
    return lines


def _draw_centered_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    y_start: int,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    image_width: int,
    line_spacing: int,
) -> int:
    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]
        x = (image_width - line_w) // 2
        draw.text((x, y), line, font=font, fill=fill)
        y += line_h + line_spacing
    return y


def render_simple_image(module: dict[str, Any], output_path: str | Path) -> None:
    width, height = 1000, 1000
    image = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(image)

    # Default font loading with optional size support where available.
    try:
        headline_font = ImageFont.load_default(size=42)
        subtext_font = ImageFont.load_default(size=24)
        overlay_font = ImageFont.load_default(size=28)
    except TypeError:
        headline_font = ImageFont.load_default()
        subtext_font = ImageFont.load_default()
        overlay_font = ImageFont.load_default()

    text_color = (0, 0, 0)
    overlay_bg = (235, 235, 235)
    content_width = 860

    headline = str(module.get("headline", "")).strip()
    subtext = str(module.get("subtext", "")).strip()
    overlay_text = str(module.get("overlay_text", "")).strip()

    headline_lines = _wrap_text(draw, headline, headline_font, content_width)[:2]
    subtext_lines = _wrap_text(draw, subtext, subtext_font, content_width)

    y = 120
    y = _draw_centered_lines(
        draw=draw,
        lines=headline_lines,
        y_start=y,
        font=headline_font,
        fill=text_color,
        image_width=width,
        line_spacing=10,
    )

    y += 24
    _draw_centered_lines(
        draw=draw,
        lines=subtext_lines,
        y_start=y,
        font=subtext_font,
        fill=text_color,
        image_width=width,
        line_spacing=8,
    )

    rect_top = height - 180
    draw.rectangle([(70, rect_top), (width - 70, height - 70)], fill=overlay_bg)

    overlay_lines = _wrap_text(draw, overlay_text, overlay_font, width - 180)
    if not overlay_lines:
        overlay_lines = [""]

    total_h = 0
    line_heights: list[int] = []
    for line in overlay_lines:
        bbox = draw.textbbox((0, 0), line, font=overlay_font)
        h = bbox[3] - bbox[1]
        line_heights.append(h)
        total_h += h
    total_h += 8 * (len(overlay_lines) - 1)

    overlay_y = rect_top + ((height - 70 - rect_top) - total_h) // 2
    for idx, line in enumerate(overlay_lines):
        bbox = draw.textbbox((0, 0), line, font=overlay_font)
        line_w = bbox[2] - bbox[0]
        x = (width - line_w) // 2
        draw.text((x, overlay_y), line, font=overlay_font, fill=text_color)
        overlay_y += line_heights[idx] + 8

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG")
