from app.agent.agent import Agent, AgentMaxIterationsError
from app.agent.thinker import AgentThinker
from app.agent.tool import Tool
from app.agent.tool_registry import ToolRegistry
from app.agent.tool_result import ToolResult
from app.agent.tools.git_blame import build_git_blame_tool
from app.agent.tools.git_diff import build_git_diff_tool
from app.agent.tools.git_history import build_git_history_tool
from app.agent.tools.git_log import build_git_log_tool
from app.ai.embeddings.factory import get_embedding, get_embedding_with_cache
from app.repositories.search_repository import vector_search
from app.services.repository_service import get_owned_repository
from app.services.scanner_service import (
    list_files,
    read_file as read_file_from_disk,
    should_ignore,
)
from app.utils.path import get_repository_path, resolve_safe_path

GREP_MAX_MATCHES = 50


def _build_search_repository_tool(repository_id: str) -> Tool:

    async def search_repository(query: str) -> ToolResult:

        query_embedding = await get_embedding_with_cache(query) 

        chunks = await vector_search(
            repository_id=repository_id,
            embedding=query_embedding,
            limit=5,
        )

        if not chunks:
            return ToolResult(
                success=True,
                content="No relevant code found.",
                metadata={"chunk_count": 0},
            )

        content = "\n\n".join(
            f"File: {chunk['file_path']}\n{chunk['content']}"
            for chunk in chunks
        )

        return ToolResult(
            success=True,
            content=content,
            metadata={"chunk_count": len(chunks)},
        )

    return Tool(
        name="search_repository",
        description="Search the indexed repository for code relevant to a query.",
        function=search_repository,
    )


def _build_read_file_tool(repository_id: str) -> Tool:
    repository_path = get_repository_path(repository_id)

    async def read_file(path: str) -> ToolResult:
        try:
            target = resolve_safe_path(repository_path, path)
        except ValueError as e:
            return ToolResult(
                success=False,
                content=str(e),
                metadata={"path": path},
            )

        if not target.is_file():
            return ToolResult(
                success=False,
                content=f"File not found: {path}",
                metadata={"path": path},
            )

        if should_ignore(target):
            return ToolResult(
                success=False,
                content=(
                    f"'{path}' is a binary or ignored file (e.g. vendored "
                    "dependency, build artifact) and cannot be read."
                ),
                metadata={"path": path},
            )

        content = read_file_from_disk(target)

        return ToolResult(
            success=True,
            content=content,
            metadata={"path": path, "size": len(content)},
        )

    return Tool(
        name="read_file",
        description=(
            "Read the full contents of one file in the repository. "
            'Argument: path (string) - file path relative to the repository '
            'root, e.g. "app/services/auth_service.py". Use search_repository '
            "or list_directory first to find the right path."
        ),
        function=read_file,
    )


def _build_list_directory_tool(repository_id: str) -> Tool:
    repository_path = get_repository_path(repository_id)

    async def list_directory(path: str = "") -> ToolResult:
        try:
            target = resolve_safe_path(repository_path, path)
        except ValueError as e:
            return ToolResult(
                success=False,
                content=str(e),
                metadata={"path": path},
            )

        if not target.is_dir():
            return ToolResult(
                success=False,
                content=f"Directory not found: {path or '.'}",
                metadata={"path": path},
            )

        entries = []

        for entry in sorted(target.iterdir()):
            if should_ignore(entry):
                continue

            kind = "directory" if entry.is_dir() else "file"
            entries.append(f"{entry.name} ({kind})")

        content = "\n".join(entries) if entries else "This directory is empty."

        return ToolResult(
            success=True,
            content=content,
            metadata={"path": path or ".", "entry_count": len(entries)},
        )

    return Tool(
        name="list_directory",
        description=(
            "List the files and subdirectories directly inside a directory "
            'of the repository (not recursive). Argument: path (string) - '
            'directory path relative to the repository root; use "" for the '
            "repository root. Useful for understanding project structure "
            "before searching or reading files."
        ),
        function=list_directory,
    )


def _build_grep_code_tool(repository_id: str) -> Tool:
    repository_path = get_repository_path(repository_id)

    async def grep_code(pattern: str) -> ToolResult:
        matches = []

        for file in list_files(repository_path):
            content = read_file_from_disk(file)

            if not content or pattern not in content:
                continue

            relative_path = str(file.relative_to(repository_path))

            for line_number, line in enumerate(content.splitlines(), start=1):
                if pattern in line:
                    matches.append(
                        f"{relative_path}:{line_number}: {line.strip()}"
                    )

        if not matches:
            return ToolResult(
                success=True,
                content=f"No matches found for '{pattern}'.",
                metadata={"match_count": 0},
            )

        truncated = len(matches) > GREP_MAX_MATCHES
        shown = matches[:GREP_MAX_MATCHES]

        content = "\n".join(shown)

        if truncated:
            content += (
                f"\n\n(showing first {GREP_MAX_MATCHES} of "
                f"{len(matches)} matches)"
            )

        return ToolResult(
            success=True,
            content=content,
            metadata={
                "match_count": len(matches),
                "truncated": truncated,
            },
        )

    return Tool(
        name="grep_code",
        description=(
            "Search the repository for an exact literal string (not "
            'semantic search). Argument: pattern (string), e.g. '
            '"JWT_SECRET". Returns matching file paths with line numbers - '
            "much faster than search_repository for finding exact symbols "
            "or config keys."
        ),
        function=grep_code,
    )


async def run_agent(
    repository_id: str,
    current_user_id: str,
    user_query: str,
):
    await get_owned_repository(repository_id, current_user_id)

    registry = ToolRegistry()
    registry.register(_build_search_repository_tool(repository_id))
    registry.register(_build_read_file_tool(repository_id))
    registry.register(_build_list_directory_tool(repository_id))
    registry.register(_build_grep_code_tool(repository_id))
    registry.register(build_git_history_tool(repository_id))
    registry.register(build_git_log_tool(repository_id))
    registry.register(build_git_diff_tool(repository_id))
    registry.register(build_git_blame_tool(repository_id))

    agent = Agent(
        registry=registry,
        thinker=AgentThinker(registry),
    )

    try:
        return await agent.run(user_query)
    except AgentMaxIterationsError:
        return (
            "I couldn't find a confident answer within the allowed "
            "number of steps. Try asking a more specific question "
            "(e.g. naming a file or feature)."
        )

async def run_agent_streaming(repository_id, current_user_id, user_query):
    await get_owned_repository(repository_id, current_user_id)

    registry = ToolRegistry()
    registry.register(_build_search_repository_tool(repository_id))
    registry.register(_build_read_file_tool(repository_id))
    registry.register(_build_list_directory_tool(repository_id))
    registry.register(_build_grep_code_tool(repository_id))
    registry.register(build_git_history_tool(repository_id))
    registry.register(build_git_log_tool(repository_id))
    registry.register(build_git_diff_tool(repository_id))
    registry.register(build_git_blame_tool(repository_id))

    agent = Agent(registry=registry, thinker=AgentThinker(registry))

    async for event in agent.run_streaming(user_query):
        yield event