from pydantic import BaseModel, Field


class RecipeIn(BaseModel):
    title: str = Field(min_length=1)
    author_name: str = Field(min_length=1)
    ingredients: list[str] = Field(default_factory=list)
    instructions: str = Field(min_length=1)
    substitutions: list[str] = Field(default_factory=list)
    tagline: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
