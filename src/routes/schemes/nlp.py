import uuid
from pydantic import BaseModel,Field
from typing import Optional

class PushRequest(BaseModel):

    do_reset:Optional[int]= 0
    
class SerachRequest(BaseModel):
    text :str
    limit : Optional[int] = 5
    session_uuid: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4)