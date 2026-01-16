from re import S
from pydantic import BaseModel
from typing import Optional

class PushRequest(BaseModel):

    do_reset:Optional[int]= 0
    
class SerachRequest(BaseModel):
    text :str
    limit : Optional[int] = 5
