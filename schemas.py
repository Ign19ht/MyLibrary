from pydantic import BaseModel


class ApproveRequest(BaseModel):
    word_id: int
    approve: int

