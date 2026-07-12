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

# A directory created by `python -m venv` / virtualenv always contains this
# marker file at its root, regardless of what the directory itself is named
# (e.g. "myenv", "env39") - name-based matching alone would always miss some.
VENV_MARKER_FILE = "pyvenv.cfg"

BINARY_FILE_EXTENSIONS = {
    ".whl", ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe", ".bin",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp", ".svg",
    ".pdf", ".zip", ".tar", ".gz", ".7z", ".rar",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".class", ".jar", ".db", ".sqlite", ".sqlite3",
    ".mp3", ".mp4", ".mov", ".avi",
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


def _is_inside_virtualenv(path: Path) -> bool:
    return any(
        (parent / VENV_MARKER_FILE).is_file()
        for parent in path.parents
    )


def _looks_binary(path: Path) -> bool:
    if path.suffix.lower() in BINARY_FILE_EXTENSIONS:
        return True

    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
    except OSError:
        return True

    return b"\x00" in chunk


def should_ignore(path: Path) -> bool:
    for part in path.parts:
        if part in IGNORED_DIRECTORIES:
            return True

    if path.name in IGNORED_FILES:
        return True

    if _is_inside_virtualenv(path):
        return True

    if path.is_file() and _looks_binary(path):
        return True

    return False


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