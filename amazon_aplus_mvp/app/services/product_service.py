import json
from pathlib import Path

from pydantic import ValidationError

from app.models.content import MasterCopyInput
from app.models.product import ProductInput


class ProductService:
    @staticmethod
    def parse_product_json(raw_json: str) -> ProductInput:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON parsing failed: {exc.msg}") from exc

        try:
            return ProductInput.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Product validation failed: {exc}") from exc

    @staticmethod
    def load_product_from_file(path: Path) -> ProductInput:
        return ProductService.parse_product_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def parse_master_copy_json(raw_json: str) -> MasterCopyInput:
        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Master copy JSON parsing failed: {exc.msg}") from exc

        try:
            return MasterCopyInput.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Master copy validation failed: {exc}") from exc
