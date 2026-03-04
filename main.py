from fastapi import FastAPI

from auth.routes.auth_router import auth_router
from user.routes.user_router import user_router

app = FastAPI(title="Personal Finance Tracker API", root_path="/api/v1")


app.include_router(auth_router)
app.include_router(user_router)
