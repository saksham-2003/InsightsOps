from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.health import (
    router as health_router
)

from api.routes.analytics import (
    router as analytics_router
)

from api.routes.agent import (
    router as agent_router
)

from api.routes.ml import (
    router as ml_router
)


app = FastAPI(
    title="InsightsOps API",

    description=(
        "AI-powered business analytics and "
        "agentic decision intelligence API"
    ),

    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://insightsops-1.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    health_router
)


app.include_router(
    analytics_router
)


app.include_router(
    agent_router
)

app.include_router(
    ml_router
)


@app.get("/")
def root():

    return {
        "message": "Welcome to InsightsOps API",
        "docs": "/docs"
    }