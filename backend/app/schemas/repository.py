from datetime import datetime

from pydantic import BaseModel, HttpUrl


class RepositoryCreate(BaseModel):
    github_url: HttpUrl


class RepositoryResponse(BaseModel):
    id: str
    github_url: HttpUrl
    name: str
    status: str
    created_at: datetime


class IndexResponse(BaseModel):
    status: str
    message: str 

class RepositoryStatusResponse(BaseModel):
    status: str
