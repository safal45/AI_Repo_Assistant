from typing import Any, Literal, Optional

from pydantic import BaseModel, model_validator


class AgentAction(BaseModel):
    action_type: Literal["tool", "final_answer"]
    tool_name: Optional[str] = None
    arguments: Optional[dict[str, Any]] = None
    answer: Optional[str] = None

    @model_validator(mode="after")
    def _validate_shape(self) -> "AgentAction":
        if self.action_type == "tool" and not self.tool_name:
            raise ValueError(
                "tool_name is required when action_type is 'tool'"
            )

        if self.action_type == "final_answer" and self.answer is None:
            raise ValueError(
                "answer is required when action_type is 'final_answer'"
            )

        return self
