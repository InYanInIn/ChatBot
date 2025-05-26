from pydantic import BaseModel

class Query(BaseModel):
    prompt: str
    model: str = "llama3.2"
    stream: bool = False
