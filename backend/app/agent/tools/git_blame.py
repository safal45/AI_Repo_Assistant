from pathlib import Path

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from app.agent.tool import Tool
from app.agent.tool_result import ToolResult
from app.utils.path import get_repository_path, resolve_safe_path

SECTION_SEPARATOR = "\n----------------------------------------------------\n\n"


def _format_section(
    commit,
    start_line: int,
    end_line: int,
    line_text: str | None,
) -> str:
    section = (
        f"Commit: {commit.hexsha[:7]}\n"
        f"Author: {commit.author.name}\n"
        f"Date: {commit.committed_datetime.date().isoformat()}\n"
        f"Affected Lines: {start_line}-{end_line}\n"
    )

    if line_text is not None:
        section += f"Line {start_line}: {line_text}\n"

    return section


async def _git_blame(
    repository_path: Path,
    file_path: str,
    line_number: int | None = None,
) -> ToolResult:
    try:
        target = resolve_safe_path(repository_path, file_path)
    except ValueError as e:
        return ToolResult(
            success=False,
            content=str(e),
            metadata={"file": file_path},
        )

    if not target.is_file():
        return ToolResult(
            success=False,
            content="File not found.",
            metadata={"file": file_path},
        )

    if line_number is not None:
        try:
            total_lines = len(target.read_text().splitlines())
        except (OSError, UnicodeDecodeError) as e:
            return ToolResult(
                success=False,
                content=f"Could not read '{file_path}': {e}",
                metadata={"file": file_path},
            )

        if line_number < 1 or line_number > total_lines:
            return ToolResult(
                success=False,
                content=(
                    f"Line {line_number} is out of range for '{file_path}' "
                    f"(file has {total_lines} lines)."
                ),
                metadata={"file": file_path},
            )

    relative_path = str(target.relative_to(repository_path.resolve()))

    try:
        repo = Repo(repository_path)

        blame_kwargs = {}
        if line_number is not None:
            blame_kwargs["L"] = f"{line_number},{line_number}"

        blame_data = repo.blame("HEAD", relative_path, **blame_kwargs)
    except (InvalidGitRepositoryError, NoSuchPathError):
        return ToolResult(
            success=False,
            content="This repository could not be opened as a Git repository.",
            metadata={"file": file_path},
        )
    except GitCommandError as e:
        return ToolResult(
            success=False,
            content=f"Failed to compute blame for '{file_path}': {e}",
            metadata={"file": file_path},
        )
    except Exception as e:
        # Defensive catch-all: this tool must never let a raw exception
        # reach the Agent loop - any unexpected failure degrades to a
        # failed ToolResult instead.
        return ToolResult(
            success=False,
            content=f"Failed to compute blame for '{file_path}': {e}",
            metadata={"file": file_path},
        )

    if not blame_data:
        return ToolResult(
            success=True,
            content=f"'{file_path}' has no blame information (the file is empty).",
            metadata={"file": file_path, "line_count": 0, "authors": []},
        )

    sections: list[str] = []
    authors: set[str] = set()

    # blame_data is a list of (Commit, [line texts]) pairs, in file
    # order, each pair covering a contiguous block of lines attributed
    # to that commit - offset tracks our position through the file (or
    # through the single requested line) to compute each block's real
    # line numbers, since GitPython does not return them directly.
    offset = line_number - 1 if line_number is not None else 0

    for commit, lines in blame_data:
        start_line = offset + 1
        end_line = offset + len(lines)
        offset = end_line

        authors.add(commit.author.name)

        line_text = lines[0] if line_number is not None else None
        sections.append(_format_section(commit, start_line, end_line, line_text))

    content = SECTION_SEPARATOR.join(sections)
    line_count = 1 if line_number is not None else offset

    return ToolResult(
        success=True,
        content=content,
        metadata={
            "file": file_path,
            "line_count": line_count,
            "authors": sorted(authors),
        },
    )


def build_git_blame_tool(repository_id: str) -> Tool:
    repository_path = get_repository_path(repository_id)

    async def git_blame(
        file_path: str,
        line_number: int | None = None,
    ) -> ToolResult:
        return await _git_blame(repository_path, file_path, line_number)

    return Tool(
        name="git_blame",
        description=(
            "Return Git blame information for a file - which commit and "
            "author last changed each line, and when. Arguments: "
            "file_path (string, required) - path relative to the "
            "repository root; line_number (integer, optional) - if "
            "given, restrict the result to that one line and include its "
            "source text; if omitted, blame the entire file line by "
            "line. Use this tool when the user asks who wrote something, "
            "who introduced a change, wants a blame report, wants the "
            "author of a specific line, or is asking about code "
            "ownership."
        ),
        function=git_blame,
    )
