from typing import Any

from pydantic import BaseModel, Field


class RecipeImport(BaseModel):
    title: str
    author_name: str
    ingredients: list[str] = Field(default_factory=list)
    instructions: str
    substitutions: list[str] = Field(default_factory=list)
    tagline: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    source_url: str | None = None
    source_platform: str | None = None


class ImportedContent(BaseModel):
    platform:str
    original_url:str
    external_id:str | None = None

    author_name:str | None = None
    title:str | None = None
    description:str | None = None

    media_type:str
    thumbnail_url:str | None = None
    media_url:str | None = None

    transcript:str | None = None
    recipe:RecipeImport | None = None
    metadata:dict[str, Any] = Field(default_factory=dict)

    status:str
