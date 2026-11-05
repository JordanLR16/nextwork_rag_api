from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Input payload for /query requests."""
    q: str = Field(min_length=1)
    n_results: int = Field(default=3, ge=1, le=10)


class AddKnowledgeRequest(BaseModel):
    """Input payload for /add requests."""
    text: str = Field(min_length=1)
