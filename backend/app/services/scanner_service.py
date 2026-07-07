from pathlib import Path

IGNORED_DIRECTORIES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "coverage",
}

IGNORED_FILES = {
    ".DS_Store",
}

LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rs": "rust",
    ".php": "php",
    ".rb": "ruby",
    ".md": "markdown",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
}


def should_ignore(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORED_DIRECTORIES:
            return True

    return path.name in IGNORED_FILES


def list_files(repository_path: Path) -> list[Path]:
    files = []

    for path in repository_path.rglob("*"):

        if not path.is_file():
            continue

        if should_ignore(path):
            continue

        files.append(path)

    return files


def read_file(path: Path) -> str:
    try:
        return path.read_text(
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        return ""


def detect_language(path: Path) -> str:
    return LANGUAGE_MAP.get(
        path.suffix.lower(),
        "text",
    )