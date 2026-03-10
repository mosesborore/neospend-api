from pydantic import BaseModel


class GenericResponse(BaseModel):
    """Generic Response Model"""

    success: bool
    msg: str


class DeleteResponse(BaseModel):
    """Delete Response Model"""

    ok: bool
