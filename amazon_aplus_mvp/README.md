# Amazon A+ Local MVP (FastAPI + Playwright)

Lokale MVP webapp voor het genereren van Amazon A+ content assets per marketplace en taal.

## Wat deze MVP doet

- Productdata inladen via JSON (plakken in UI of sample laden)
- Marketplace-selectie (DE, FR, NL, IT, ES)
- Mock AI copy genereren per marketplace
- 5 vaste A+ templates renderen naar PNG via Playwright:
  - hero
  - body_mapping
  - problem_solution
  - features
  - compatibility
- Export per marketplace met `copy.json` + PNG assets
- Resultaatpagina met previews

## Tech stack

- Python 3.11+
- FastAPI
- Jinja2
- Uvicorn
- Playwright (Chromium)
- Pydantic

## Projectstructuur

```text
app/
  main.py
  config.py
  routes/
    pages.py
    api.py
  services/
    ai_service.py
    render_service.py
    export_service.py
    product_service.py
  models/
    product.py
    content.py
  templates/
    base.html
    index.html
    result.html
    partials/
      render_css.html
    aplus/
      hero.html
      body_mapping.html
      problem_solution.html
      features.html
      compatibility.html
  static/
    css/
      styles.css
    uploads/
    exports/
  utils/
    file_helpers.py
    slugify.py
  sample_data/
    sample_product.json
requirements.txt
README.md
```

## Installatie

1. Maak en activeer een virtuele omgeving.
2. Installeer dependencies:

```bash
pip install -r requirements.txt
```

3. Installeer Playwright browser:

```bash
playwright install chromium
```

## Starten

```bash
uvicorn app.main:app --reload
```

Open daarna:

- http://127.0.0.1:8000/

## MVP flow

1. Open homepage
2. Gebruik sample JSON of plak eigen JSON
3. Selecteer marketplaces
4. Klik op generate
5. De app maakt mock copy + rendert 5 PNG templates per marketplace
6. Resultaten staan in:

```text
app/static/exports/<product_slug>/<marketplace>/
```

Met per marketplace:

- `hero.png`
- `body_mapping.png`
- `problem_solution.png`
- `features.png`
- `compatibility.png`
- `copy.json`

## API endpoint

`POST /api/generate`

Payload voorbeeld:

```json
{
  "product": {
    "product_name": "TENS/EMS Electrode Pads Pro",
    "brand_name": "Motron Care",
    "short_description": "Premium hydrogel electrode pads",
    "usps": ["Strong conductivity"],
    "compatibility": ["2mm pin TENS units"],
    "use_cases": ["Post-workout recovery"],
    "target_audience": "active adults",
    "tone_of_voice": "premium",
    "forbidden_claims": ["cure"],
    "allowed_marketplaces": ["DE", "FR", "NL"],
    "image_paths": {
      "product_image": "",
      "logo_image": "",
      "lifestyle_image": ""
    }
  },
  "marketplaces": ["DE", "FR"]
}
```

## Uitbreiden naar echte AI

Pas `app/services/ai_service.py` aan:

- `generate_marketplace_copy(...)`
- `rewrite_copy_for_marketplace(...)`
- `validate_claims(...)`

Daar kun je later eenvoudig OpenAI prompts/API-calls toevoegen.

## Notities

- Geen database/auth/queue/cloud in deze MVP
- Lokale bestandsopslag in `app/static/exports`
- Bij ontbrekende velden gebruikt de app defaults waar mogelijk
