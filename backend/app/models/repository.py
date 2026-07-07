from datetime import datetime

from pydantic import BaseModel, Field


class Repository(BaseModel):
    owner_id: str

    github_url: str

    name: str

    default_branch: str = "main"

    status: str = "pending"

    created_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    updated_at: datetime = Field(
        default_factory=datetime.utcnow
    )