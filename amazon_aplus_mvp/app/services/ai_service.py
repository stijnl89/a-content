import json
import logging
import re
from urllib import error as urlerror
from urllib import request as urlrequest

from app.config import DEFAULT_MODEL, OPENAI_API_KEY
from app.models.content import BenefitBlock, MarketplaceContent, MasterCopyInput
from app.models.product import ProductInput

logger = logging.getLogger(__name__)


class AIContentService:
    """
    Hybrid AI service:
    - Rewrite mode: rewrite/localize a provided master copy per marketplace.
    - Generate mode: generate localized copy from product data.
    """

    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

    MARKET_TONE = {
        "FR": "fluent, premium, reassuring",
        "DE": "clear, structured, rational",
        "NL": "direct, clear, practical",
        "IT": "warm, smooth, consumer-friendly",
        "ES": "accessible, natural, slightly dynamic",
    }

    # Heuristic warning list for accidental English leakage in non-EN outputs.
    ENGLISH_MARKERS = {
        "the",
        "and",
        "with",
        "for",
        "from",
        "daily",
        "comfortable",
        "friendly",
        "solution",
        "problem",
        "feature",
        "compatible",
        "recovery",
        "benefit",
    }

    LOCALIZED_COPY = {
        "DE": {
            "hero_headline": "Komfortable TENS/EMS-Pads fur jeden Tag",
            "hero_subtext": "Hautfreundliche Hydrogel-Elektroden fur eine gleichmassige Stimulation zu Hause, im Studio und unterwegs.",
            "benefit_titles": [
                "Konstante Leitfahigkeit",
                "Angenehm auf der Haut",
                "Zuverlassiger Halt",
                "Flexible Anwendung",
            ],
            "benefit_texts": [
                "Gleichmassige Impulsweitergabe fur eine stabile Anwendung.",
                "Sanftes Tragegefuhl auch bei wiederholter Nutzung.",
                "Sicherer Sitz wahrend Ruhe, Arbeit und Bewegung.",
                "Geeignet fur Nacken, Rucken, Schultern und Beine.",
            ],
            "problem_title": "Muskelverspannungen bremsen den Alltag",
            "problem_text": "Langes Sitzen, intensive Belastung und wiederholte Bewegungen fuhren oft zu Spannungsgefuhlen.",
            "solution_title": "Gezielte Impulse mit klarem Fokus",
            "solution_text": "Die Pads ubertragen TENS/EMS-Impulse gleichmassig und unterstutzen eine planbare Regenerationsroutine.",
            "module_texts": {
                "hero": "Premium-Qualitat fur eine verlassliche Anwendung im Alltag.",
                "body_mapping": "Jeder Vorteil unterstutzt ein konkretes Komfort- und Bewegungsziel.",
                "problem_solution": "Von Belastung zu strukturierter Erholung in wenigen Schritten.",
                "features": "Langlebige Materialien, einfache Handhabung und sauberer Sitz.",
                "compatibility": "Kompatibel mit vielen gangigen Geraten mit 2-mm-Anschluss.",
            },
            "fallback_compatibility": [
                "TENS-Gerate mit 2-mm-Pin",
                "EMS-Gerate mit 2-mm-Pin",
                "Viele Heimtherapie-Systeme",
                "Tragbare Reha-Gerate",
            ],
            "fallback_use_cases": [
                "Regeneration nach dem Training",
                "Unterstutzung bei Nacken- und Ruckenverspannungen",
                "Ausgleich nach langem Sitzen",
                "Komfort auf Reisen",
            ],
        },
        "FR": {
            "hero_headline": "Electrodes TENS/EMS premium pour un soulagement quotidien",
            "hero_subtext": "Des patchs hydrogel doux pour la peau, concus pour une stimulation stable a la maison comme en deplacement.",
            "benefit_titles": [
                "Conductivite reguliere",
                "Confort cutane durable",
                "Maintien fiable",
                "Utilisation polyvalente",
            ],
            "benefit_texts": [
                "Transmission homogene des impulsions pour une utilisation reguliere.",
                "Sensation douce sur la peau, meme en usage frequent.",
                "Tenue stable pendant les activites quotidiennes.",
                "Application adaptee au cou, au dos, aux epaules et aux jambes.",
            ],
            "problem_title": "Les tensions musculaires perturbent le rythme quotidien",
            "problem_text": "Le travail assis, les efforts repetes et l'activite sportive peuvent provoquer des zones de tension persistantes.",
            "solution_title": "Une stimulation ciblee, simple a integrer",
            "solution_text": "Les electrodes diffusent les impulsions TENS/EMS de facon homogene pour soutenir le confort et la recuperation.",
            "module_texts": {
                "hero": "Une finition premium pour une routine bien-etre plus sereine.",
                "body_mapping": "Chaque benefice repond a un besoin concret d'usage.",
                "problem_solution": "Passez de la tension a une recuperation mieux maitrisee.",
                "features": "Materiaux de qualite, application facile et sensation confortable.",
                "compatibility": "Compatible avec de nombreux appareils TENS/EMS a connecteur 2 mm.",
            },
            "fallback_compatibility": [
                "Appareils TENS a pin 2 mm",
                "Stimulateurs EMS a pin 2 mm",
                "La plupart des dispositifs d'electrotherapie domestique",
                "Unites de reeducation portables",
            ],
            "fallback_use_cases": [
                "Recuperation apres le sport",
                "Soutien en cas de tensions cervicales et dorsales",
                "Confort apres une longue journee assise",
                "Gestion de l'inconfort en voyage",
            ],
        },
        "NL": {
            "hero_headline": "Premium TENS/EMS elektroden voor dagelijks comfort",
            "hero_subtext": "Huidvriendelijke hydrogel pads met stabiele geleiding voor thuisgebruik, herstelmomenten en onderweg.",
            "benefit_titles": [
                "Stabiele geleiding",
                "Comfortabel op de huid",
                "Betrouwbare kleefkracht",
                "Breed inzetbaar",
            ],
            "benefit_texts": [
                "Gelijkmatige overdracht van impulsen voor consistente stimulatie.",
                "Zachte ervaring op de huid, ook bij vaker gebruik.",
                "Blijft stevig zitten tijdens dagelijkse activiteiten.",
                "Geschikt voor nek, rug, schouders en benen.",
            ],
            "problem_title": "Spierbelasting stapelt zich snel op",
            "problem_text": "Lang zitten, intensief trainen en herhaalde bewegingen zorgen vaak voor aanhoudende spanning.",
            "solution_title": "Gerichte stimulatie zonder gedoe",
            "solution_text": "De pads verdelen TENS/EMS impulsen gelijkmatig en maken je herstelroutine consistenter en comfortabeler.",
            "module_texts": {
                "hero": "Premium kwaliteit voor een betrouwbare dagelijkse routine.",
                "body_mapping": "Elk voordeel sluit aan op een concreet gebruiksmoment.",
                "problem_solution": "Van opgebouwde spanning naar gecontroleerd herstel.",
                "features": "Duurzame materialen, eenvoudig aan te brengen en prettig in gebruik.",
                "compatibility": "Geschikt voor veel TENS/EMS apparaten met 2 mm aansluiting.",
            },
            "fallback_compatibility": [
                "TENS apparaten met 2 mm pin",
                "EMS apparaten met 2 mm pin",
                "Veel thuis elektrotherapie systemen",
                "Draagbare revalidatie units",
            ],
            "fallback_use_cases": [
                "Herstel na het sporten",
                "Ondersteuning bij nek- en rugspanning",
                "Comfort na lange kantoordagen",
                "Gebruiksvriendelijk onderweg",
            ],
        },
        "IT": {
            "hero_headline": "Elettrodi TENS/EMS premium per il benessere quotidiano",
            "hero_subtext": "Patch in idrogel delicati sulla pelle, progettati per una stimolazione uniforme a casa e in movimento.",
            "benefit_titles": [
                "Conducibilita costante",
                "Comfort sulla pelle",
                "Aderenza affidabile",
                "Uso versatile",
            ],
            "benefit_texts": [
                "Trasferimento uniforme degli impulsi per una stimolazione regolare.",
                "Sensazione delicata sulla pelle anche con uso frequente.",
                "Tenuta stabile durante le attivita quotidiane.",
                "Adatti a collo, schiena, spalle e gambe.",
            ],
            "problem_title": "La tensione muscolare limita la routine",
            "problem_text": "Sedentarieta, allenamenti intensi e movimenti ripetitivi possono causare fastidi e irrigidimento.",
            "solution_title": "Stimolazione mirata, integrazione semplice",
            "solution_text": "Gli elettrodi distribuiscono gli impulsi TENS/EMS in modo omogeneo per supportare comfort e recupero.",
            "module_texts": {
                "hero": "Qualita premium per un utilizzo regolare e affidabile.",
                "body_mapping": "Ogni beneficio risponde a un'esigenza pratica.",
                "problem_solution": "Dalla tensione al recupero con una routine piu ordinata.",
                "features": "Materiali di qualita, applicazione semplice e sensazione piacevole.",
                "compatibility": "Compatibile con molti dispositivi TENS/EMS con connettore da 2 mm.",
            },
            "fallback_compatibility": [
                "Dispositivi TENS con pin da 2 mm",
                "Stimolatori EMS con pin da 2 mm",
                "Molti sistemi di elettroterapia domestica",
                "Unita riabilitative portatili",
            ],
            "fallback_use_cases": [
                "Recupero post allenamento",
                "Supporto per tensioni a collo e schiena",
                "Sollievo dopo molte ore seduti",
                "Gestione del comfort in viaggio",
            ],
        },
        "ES": {
            "hero_headline": "Electrodos TENS/EMS premium para confort diario",
            "hero_subtext": "Parches de hidrogel suaves con la piel para una estimulacion estable en casa, en trabajo y en movimiento.",
            "benefit_titles": [
                "Conduccion uniforme",
                "Comodidad cutanea",
                "Adherencia fiable",
                "Uso versatil",
            ],
            "benefit_texts": [
                "Transferencia homogenea de impulsos para una estimulacion estable.",
                "Sensacion agradable en la piel incluso con uso repetido.",
                "Fijacion segura durante la rutina diaria.",
                "Aptos para cuello, espalda, hombros y piernas.",
            ],
            "problem_title": "La tension muscular afecta el rendimiento diario",
            "problem_text": "Muchas horas sentado, entrenamientos exigentes y movimientos repetitivos suelen generar molestias.",
            "solution_title": "Estimulo dirigido, rutina mas constante",
            "solution_text": "Los electrodos distribuyen impulsos TENS/EMS de forma homogenea para apoyar comodidad y recuperacion.",
            "module_texts": {
                "hero": "Acabado premium para una experiencia de uso mas confiable.",
                "body_mapping": "Cada beneficio se conecta con una necesidad real de uso.",
                "problem_solution": "De la tension a una recuperacion mejor organizada.",
                "features": "Materiales duraderos, aplicacion sencilla y ajuste comodo.",
                "compatibility": "Compatible con muchos equipos TENS/EMS con conector de 2 mm.",
            },
            "fallback_compatibility": [
                "Equipos TENS con pin de 2 mm",
                "Estimuladores EMS con pin de 2 mm",
                "La mayoria de dispositivos domesticos de electroterapia",
                "Unidades portatiles de rehabilitacion",
            ],
            "fallback_use_cases": [
                "Recuperacion despues del entrenamiento",
                "Apoyo para tension cervical y lumbar",
                "Confort tras jornadas largas sentado",
                "Gestion de molestias durante viajes",
            ],
        },
    }

    def _localized_profile(self, marketplace: str) -> dict:
        return self.LOCALIZED_COPY.get(marketplace, self.LOCALIZED_COPY["NL"])

    def _all_text_fields(self, payload: dict) -> list[str]:
        values: list[str] = []

        def walk(node: object) -> None:
            if isinstance(node, str):
                values.append(node)
            elif isinstance(node, dict):
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(payload)
        return values

    def _contains_english_markers(self, payload: dict) -> bool:
        text_blob = " ".join(self._all_text_fields(payload)).lower()
        tokens = set(re.findall(r"\b[a-z]{2,}\b", text_blob))
        return bool(tokens.intersection(self.ENGLISH_MARKERS))

    def _build_export_text_by_template(self, content: MarketplaceContent) -> dict[str, dict[str, str]]:
        return {
            "hero": {
                "headline": content.hero_headline,
                "subtext": content.hero_subtext,
            },
            "body_mapping": {
                key: value
                for idx, block in enumerate(content.benefit_blocks)
                for key, value in (
                    (f"benefit_{idx + 1}_title", block.title),
                    (f"benefit_{idx + 1}_text", block.text),
                )
            },
            "problem_solution": {
                "problem_title": content.problem_title,
                "problem_text": content.problem_text,
                "solution_title": content.solution_title,
                "solution_text": content.solution_text,
            },
            "features": {
                "feature_text": content.module_texts.get("features", ""),
            },
            "compatibility": {
                "compatibility": " | ".join(content.compatibility_points),
                "use_cases": " | ".join(content.use_case_points),
            },
        }

    def _normalize_rewrite_payload(self, payload: dict, marketplace: str) -> MarketplaceContent:
        source_like = MasterCopyInput.model_validate(payload)
        content = MarketplaceContent(
            marketplace=marketplace,
            hero_headline=source_like.hero_headline,
            hero_subtext=source_like.hero_subtext,
            benefit_blocks=source_like.benefit_blocks,
            problem_title=source_like.problem_title,
            problem_text=source_like.problem_text,
            solution_title=source_like.solution_title,
            solution_text=source_like.solution_text,
            compatibility_points=source_like.compatibility_points,
            use_case_points=source_like.use_case_points,
            module_texts=source_like.module_texts,
            export_text_by_template=source_like.export_text_by_template,
        )
        if not content.export_text_by_template:
            content.export_text_by_template = self._build_export_text_by_template(content)
        return content

    def _openai_chat_completion(self, system_prompt: str, user_prompt: str, temperature: float = 0.25) -> str:
        if not OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY ontbreekt in environment/.env")

        body = {
            "model": DEFAULT_MODEL,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        req = urlrequest.Request(
            self.OPENAI_API_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlrequest.urlopen(req, timeout=90) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urlerror.HTTPError as exc:
            error_text = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            raise RuntimeError(f"OpenAI rewrite request failed: {error_text}") from exc
        except Exception as exc:
            raise RuntimeError(f"OpenAI rewrite request failed: {exc}") from exc

        try:
            return payload["choices"][0]["message"]["content"]
        except Exception as exc:
            raise RuntimeError(f"Unexpected OpenAI response format: {payload}") from exc

    def _generate_marketplace_copy_fallback(self, product: ProductInput, marketplace: str) -> MarketplaceContent:
        profile = self._localized_profile(marketplace)
        product_label = product.product_name or "TENS/EMS electrode pads"
        brand_label = product.brand_name or "Brand"

        benefits = [
            BenefitBlock(title=profile["benefit_titles"][idx], text=profile["benefit_texts"][idx])
            for idx in range(4)
        ]

        content = MarketplaceContent(
            marketplace=marketplace,
            hero_headline=f"{brand_label} {product_label} - {profile['hero_headline']}",
            hero_subtext=profile["hero_subtext"],
            benefit_blocks=benefits,
            problem_title=profile["problem_title"],
            problem_text=profile["problem_text"],
            solution_title=profile["solution_title"],
            solution_text=profile["solution_text"],
            compatibility_points=profile["fallback_compatibility"][:6],
            use_case_points=profile["fallback_use_cases"][:6],
            module_texts=profile["module_texts"],
            export_text_by_template={},
        )
        content.export_text_by_template = self._build_export_text_by_template(content)
        return content

    def _rewrite_marketplace_copy_fallback(
        self,
        source_copy: MasterCopyInput,
        marketplace: str,
    ) -> MarketplaceContent:
        logger.warning(
            "OPENAI_API_KEY ontbreekt of rewrite-call faalde. Rewrite mode gedeactiveerd; generate fallback gebruikt voor %s.",
            marketplace,
        )
        profile = self._localized_profile(marketplace)

        benefits = [
            BenefitBlock(
                title=profile["benefit_titles"][idx],
                text=profile["benefit_texts"][idx],
            )
            for idx in range(4)
        ]

        content = MarketplaceContent(
            marketplace=marketplace,
            hero_headline=profile["hero_headline"],
            hero_subtext=profile["hero_subtext"],
            benefit_blocks=benefits,
            problem_title=profile["problem_title"],
            problem_text=profile["problem_text"],
            solution_title=profile["solution_title"],
            solution_text=profile["solution_text"],
            compatibility_points=(source_copy.compatibility_points or profile["fallback_compatibility"])[:6],
            use_case_points=(source_copy.use_case_points or profile["fallback_use_cases"])[:6],
            module_texts=(source_copy.module_texts or profile["module_texts"]),
            export_text_by_template={},
        )
        content.export_text_by_template = self._build_export_text_by_template(content)
        return content

    def rewrite_marketplace_copy_with_openai(
        self,
        source_copy: MasterCopyInput,
        marketplace: str,
    ) -> MarketplaceContent:
        tone = self.MARKET_TONE.get(marketplace, "clear and natural")
        logger.info("Rewrite mode actief voor marketplace %s met model %s", marketplace, DEFAULT_MODEL)

        system_prompt = (
            "You are a native Amazon copywriter for the target marketplace. "
            "Rewrite product copy in fluent native language while preserving structure and meaning. "
            "Always return valid JSON only."
        )

        user_prompt = (
            f"Target marketplace: {marketplace}\n"
            f"Tone: {tone}\n\n"
            "Rewrite rules:\n"
            "- You are a native Amazon copywriter for the target marketplace.\n"
            "- Rewrite the provided product copy into fluent, natural language.\n"
            "- Do NOT translate literally.\n"
            "- Rewrite it as if it was originally written in that language.\n"
            "- Keep all product claims, meaning and structure identical.\n"
            "- Keep the same number of benefit blocks.\n"
            "- Do not invent new features or claims.\n"
            "- Use correct grammar, spelling and accents.\n"
            "- No English words are allowed in the output.\n"
            "- Rewrite ALL fields: hero_headline, hero_subtext, benefit_blocks, problem/solution, "
            "compatibility_points, use_case_points, module_texts, export_text_by_template.\n"
            "- Output must be valid JSON with EXACTLY the same structure as the input JSON.\n\n"
            f"Source JSON:\n{json.dumps(source_copy.model_dump(), ensure_ascii=False, indent=2)}"
        )

        raw_content = self._openai_chat_completion(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = json.loads(raw_content)
        rewritten = self._normalize_rewrite_payload(parsed, marketplace)

        if self._contains_english_markers(rewritten.model_dump()):
            logger.warning("English markers detected in rewrite output for marketplace %s", marketplace)

        return rewritten

    def generate_marketplace_copy_with_openai(self, product: ProductInput, marketplace: str) -> MarketplaceContent:
        return self._generate_marketplace_copy_fallback(product, marketplace)

    def generate_marketplace_copy(self, product: ProductInput, marketplace: str) -> MarketplaceContent:
        return self._generate_marketplace_copy_fallback(product, marketplace)

    def rewrite_marketplace_copy(
        self,
        source_copy: MasterCopyInput,
        product: ProductInput,
        marketplace: str,
    ) -> MarketplaceContent:
        _ = product
        if not OPENAI_API_KEY:
            return self._rewrite_marketplace_copy_fallback(source_copy, marketplace)

        try:
            return self.rewrite_marketplace_copy_with_openai(source_copy=source_copy, marketplace=marketplace)
        except Exception as exc:
            logger.warning("Rewrite mode failed for marketplace %s: %s", marketplace, exc)
            return self._rewrite_marketplace_copy_fallback(source_copy, marketplace)

    def validate_claims(self, copy: MarketplaceContent, forbidden_claims: list[str]) -> MarketplaceContent:
        if not forbidden_claims:
            return copy

        blocked_words = [item.lower() for item in forbidden_claims if item.strip()]

        def scrub(text: str) -> str:
            clean = text
            for word in blocked_words:
                clean = clean.replace(word, "[redacted]")
                clean = clean.replace(word.capitalize(), "[redacted]")
                clean = clean.replace(word.upper(), "[redacted]")
            return clean

        copy.hero_headline = scrub(copy.hero_headline)
        copy.hero_subtext = scrub(copy.hero_subtext)
        copy.problem_text = scrub(copy.problem_text)
        copy.solution_text = scrub(copy.solution_text)
        for block in copy.benefit_blocks:
            block.text = scrub(block.text)
        copy.compatibility_points = [scrub(item) for item in copy.compatibility_points]
        copy.use_case_points = [scrub(item) for item in copy.use_case_points]
        copy.module_texts = {key: scrub(value) for key, value in copy.module_texts.items()}
        copy.export_text_by_template = self._build_export_text_by_template(copy)

        if self._contains_english_markers(copy.model_dump()):
            logger.warning("English markers detected after claim validation for marketplace %s", copy.marketplace)

        return copy
