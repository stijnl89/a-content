from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ImagePaths(BaseModel):
    product_image: Optional[str] = None
    logo_image: Optional[str] = None
    lifestyle_image: Optional[str] = None


class ProductInput(BaseModel):
    product_name: str = Field(min_length=2)
    brand_name: str = Field(min_length=2)
    short_description: str = ""
    usps: list[str] = Field(default_factory=list)
    compatibility: list[str] = Field(default_factory=list)
    use_cases: list[str] = Field(default_factory=list)
    target_audience: str = ""
    tone_of_voice: str = "professional"
    forbidden_claims: list[str] = Field(default_factory=list)
    allowed_marketplaces: list[str] = Field(default_factory=lambda: ["DE", "FR", "NL", "IT", "ES"])
    image_paths: ImagePaths = Field(default_factory=ImagePaths)

    @field_validator("allowed_marketplaces")
    @classmethod
    def normalize_marketplaces(cls, value: list[str]) -> list[str]:
        return [item.strip().upper() for item in value if item and item.strip()]
