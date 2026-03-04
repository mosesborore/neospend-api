from pydantic import BaseModel


class PrevRefreshToken(BaseModel):
    refresh_token: str
