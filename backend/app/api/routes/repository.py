import json

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from app.services.scanner_service import list_files, detect_language
from app.services.parser_service import parse_python_file
from app.utils.path import get_repository_path
from app.dependencies.auth import get_current_user
from app.schemas.repository import (
    IndexResponse,
    RepositoryCreate,
    RepositoryResponse,
    RepositoryStatusResponse
)
from app.services.repository_service import (
    create_new_repository,
    get_owned_repository,
    list_owned_repositories,
)
from app.services.indexing_service import index_repository
from app.services.embedding_service import generate_embeddings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import chat
from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_service import run_agent,run_agent_streaming
from app.tasks.indexing_task import index_repository_task
from app.repositories.repository_repository import update_repository_status


router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"],
)


@router.post(
    "",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_repository(
    repository: RepositoryCreate,
    current_user=Depends(get_current_user),
):
    return await create_new_repository(
        repository,
        current_user,
    )

@router.get(
    "",
    response_model=list[RepositoryResponse],
)
async def list_repositories(
    current_user=Depends(get_current_user),
):
    return await list_owned_repositories(str(current_user["_id"]))

@router.get("/{repository_id}/scan")
async def scan_repository(
    repository_id: str,
    current_user=Depends(get_current_user),
):
    await get_owned_repository(
        repository_id,
        str(current_user["_id"]),
    )

    repository_path = get_repository_path(repository_id)

    files = list_files(repository_path)

    return [
        {
            "path": str(file.relative_to(repository_path)),
            "language": detect_language(file),
        }
        for file in files
    ]

@router.get("/{repository_id}/chunks")
async def parse_repository(
    repository_id: str,
    current_user=Depends(get_current_user),
):
    await get_owned_repository(
        repository_id,
        str(current_user["_id"]),
    )

    repository_path = get_repository_path(repository_id)

    files = list_files(repository_path)

    chunks = []

    for file in files:

        chunks.extend(
            parse_python_file(
                repository_id,
                file,
                repository_path,
            )
        )

    return chunks
@router.post(
    "/{repository_id}/index",
    response_model=IndexResponse,
)
async def index_repository_route(
    repository_id: str,
    current_user=Depends(get_current_user),
):
    # 1. Ownership check — YE ZAROORI HAI (soch kyun, neeche)
    await get_owned_repository(repository_id, str(current_user["_id"]))
    
    # 2. Status "pending" set kar
    await update_repository_status(repository_id, "pending")
    
    # 3. Task queue mein daal (await NAHI — .delay() sync hai)
    index_repository_task.delay(repository_id, str(current_user["_id"]))
    
    # 4. Turant return
    return IndexResponse(
        status="pending",
        message="Indexing started",
    )


@router.get(
    "/{repository_id}/status",
    response_model=RepositoryStatusResponse,
)
async def get_repository_status_route(
    repository_id: str,
    current_user=Depends(get_current_user),
):
    repository = await get_owned_repository(
        repository_id,
        str(current_user["_id"]),
    )

    return RepositoryStatusResponse(
        status=repository["status"],
    )
    
@router.post("/{repository_id}/embed")
async def embed_repository(
    repository_id: str,
    current_user=Depends(get_current_user),
):
    return await generate_embeddings(
        repository_id,
        str(current_user["_id"]),
    )

@router.post(
    "/{repository_id}/chat",
    response_model=ChatResponse,
)
async def chat_with_repository(
    repository_id: str,
    request: ChatRequest,
    current_user=Depends(get_current_user),
):
    return await chat(
        repository_id=repository_id,
        current_user_id=str(current_user["_id"]),
        question=request.question,
    )

@router.post(
    "/{repository_id}/agent",
    response_model=AgentResponse,
)
async def agent_query_repository(
    repository_id: str,
    request: AgentRequest,
    current_user=Depends(get_current_user),
):
    answer = await run_agent(
        repository_id=repository_id,
        current_user_id=str(current_user["_id"]),
        user_query=request.question,
    )

    return AgentResponse(answer=answer)


@router.post("/{repository_id}/agent/stream")
async def agent_query_repository_stream(
    repository_id: str,
    request: AgentRequest,
    current_user=Depends(get_current_user),
):
    async def event_generator():
        async for event in run_agent_streaming(
            repository_id=repository_id,
            current_user_id=str(current_user["_id"]),
            user_query=request.question,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )