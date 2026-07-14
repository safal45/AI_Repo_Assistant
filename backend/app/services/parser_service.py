import ast
from pathlib import Path

from app.models.code_chunk import CodeChunk
from app.services.scanner_service import (
    detect_language,
    read_file,
)


def parse_python_file(
    repository_id: str,
    path: Path,
    repository_path: Path,
) -> list[CodeChunk]:
    """
    Parse a Python file and extract classes/functions as CodeChunks.
    """

    source = read_file(path)

    if not source:
        return []

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    language = detect_language(path)

    lines = source.splitlines()

    chunks: list[CodeChunk] = []

    for node in ast.walk(tree):

        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):

            start = node.lineno
            end = node.end_lineno or start

            content = "\n".join(
                lines[start - 1 : end]
            )

            if isinstance(node, ast.ClassDef):
                symbol_type = "class"

            elif isinstance(node, ast.AsyncFunctionDef):
                symbol_type = "async_function"

            else:
                symbol_type = "function"

            chunks.append(
                CodeChunk(
                    repository_id=repository_id,
                    file_path=str(path.relative_to(repository_path)),
                    language=language,
                    symbol=node.name,
                    symbol_type=symbol_type,
                    start_line=start,
                    end_line=end,
                    content=content,
                )
            )

    return chunks