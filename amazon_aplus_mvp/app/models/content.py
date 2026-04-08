from pydantic import BaseModel, Field, field_validator


class BenefitBlock(BaseModel):
    title: str
    text: str


class MarketplaceContent(BaseModel):
    marketplace: str
    hero_headline: str
    hero_subtext: str
    benefit_blocks: list[BenefitBlock] = Field(default_factory=list)
    problem_title: str
    problem_text: str
    solution_title: str
    solution_text: str
    compatibility_points: list[str] = Field(default_factory=list)
    use_case_points: list[str] = Field(default_factory=list)
    module_texts: dict[str, str] = Field(default_factory=dict)
    export_text_by_template: dict[str, dict[str, str]] = Field(default_factory=dict)


class MasterCopyInput(BaseModel):
    hero_headline: str
    hero_subtext: str
    benefit_blocks: list[BenefitBlock] = Field(default_factory=list)
    problem_title: str
    problem_text: str
    solution_title: str
    solution_text: str
    compatibility_points: list[str] = Field(default_factory=list)
    use_case_points: list[str] = Field(default_factory=list)
    module_texts: dict[str, str] = Field(default_factory=dict)
    export_text_by_template: dict[str, dict[str, str]] = Field(default_factory=dict)

    @field_validator("benefit_blocks")
    @classmethod
    def validate_benefit_blocks(cls, value: list[BenefitBlock]) -> list[BenefitBlock]:
        if len(value) != 4:
            raise ValueError("Master copy must contain exactly 4 benefit_blocks.")
        return value


class TemplateRenderPayload(BaseModel):
    template_name: str
    output_filename: str
    width: int
    height: int
    data: dict


class MarketplaceExport(BaseModel):
    marketplace: str
    copy_path: str
    copy_url: str = ""
    copy_content: dict = Field(default_factory=dict)
    image_paths: list[str] = Field(default_factory=list)
    preview_urls: list[str] = Field(default_factory=list)


class ExportResult(BaseModel):
    product_slug: str
    exports_dir: str
    marketplaces: list[MarketplaceExport] = Field(default_factory=list)
