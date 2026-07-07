from pydantic import BaseModel


class CodeChunk(BaseModel):
    repository_id: str

    file_path: str
    language: str

    symbol: str
    symbol_type: str

    start_line: int
    end_line: int

    content: str

    embedding: list[float] | None = None