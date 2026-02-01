from fastapi import FastAPI

from api.database import init_db
from api.routes.auth import router as auth_router

app = FastAPI(title="Personal Finance Tracker API")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth_router)
