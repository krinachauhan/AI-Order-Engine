from fastapi import FastAPI
from routers import menu, chat

app = FastAPI(title="Order Engine API")

# Include routes
app.include_router(menu.router, prefix="/api", tags=["Menu"])
app.include_router(chat.router, prefix="/api", tags=["Order"])
# app.include_router(fuzzy_routes.router, prefix="/api", tags=["Fuzzy"])

@app.get("/")
def home():
    return {"message": "Order Engine API Running!"}
