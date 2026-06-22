from pydantic import BaseModel, Field


class ComposeRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    style: str = Field(min_length=1, max_length=120)
    idea: str = Field(default="", max_length=500)


class ComposeResponse(BaseModel):
    prompt: str
    negative_prompt: str
    ratio: str
    saved: bool = False


class PromptPreferenceRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    style: str = Field(min_length=1, max_length=120)
    prompt: str = Field(default="", max_length=1500)
    negative_prompt: str = Field(default="", max_length=1500)


class OptimizePromptRequest(PromptPreferenceRequest):
    idea: str = Field(default="", max_length=500)


class GenerateRequest(ComposeRequest):
    prompt: str | None = Field(default=None, max_length=1500)
    negative_prompt: str | None = Field(default=None, max_length=1500)


class GenerateResponse(BaseModel):
    id: int
    image_url: str
    prompt: str
    negative_prompt: str
    provider: str


class GenerateIdeaRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=80)
    style: str = Field(min_length=1, max_length=120)


class GenerateIdeaResponse(BaseModel):
    idea: str
