from pydantic import BaseModel

__doc__ = """Collection of Response model that aren't related to the DB"""

__slots__ = ("msg", "ok")


class GenericResponse(BaseModel):
    msg: str


class DeleteResponse(BaseModel):
    ok: bool
