from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine

# Import models so they're registered on Base before create_all runs
from app.models import chat, diet, report, user, vitals  # noqa: F401

from app.api.routes import auth, chat as chat_routes, diet as diet_routes, reports, vitals as vitals_routes

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for MediMate: health chatbot, report analysis, "
    "diet planning, and vitals/schedule management.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # MVP: auto-create tables. Switch to Alembic migrations before production use
    # with real user data, so schema changes don't require dropping tables.
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/health")
def health():
    return {"status": "healthy"}


app.include_router(auth.router)
app.include_router(chat_routes.router)
app.include_router(reports.router)
app.include_router(vitals_routes.router)
app.include_router(diet_routes.router)
