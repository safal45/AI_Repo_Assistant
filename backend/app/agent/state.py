from pydantic import BaseModel, Field

from app.agent.observation import Observation


class AgentState(BaseModel):
    user_query: str

    observations: list[Observation] = Field(default_factory=list)

    completed: bool = False