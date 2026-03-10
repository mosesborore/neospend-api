from fastapi import FastAPI

from account.routes.account_router import account_router
from auth.routes.auth_router import auth_router
from category.routes.category_router import category_router
from user.routes.user_router import user_router

app = FastAPI(title="Personal Finance Tracker API", root_path="/api/v1")


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(account_router)
app.include_router(category_router)
