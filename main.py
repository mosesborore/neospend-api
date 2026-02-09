from fastapi import FastAPI

from api.database import init_db
from api.routes.accounts import router as accounts_router
from api.routes.auth import router as auth_router
from api.routes.categories import router as categories_router
from api.routes.transactions import router as transactions_router

app = FastAPI(title="Personal Finance Tracker API", root_path="/api/v1")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth_router, tags=["auth"])
app.include_router(accounts_router, tags=["accounts"])
app.include_router(categories_router, tags=["categories"])
app.include_router(transactions_router, tags=["transactions"])
