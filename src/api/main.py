from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router as search_router
from src.api.routes_meta import router as meta_router
from src.db.connection import close
from src.db.schema import init_schema


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_schema()
    yield
    close()


app = FastAPI(
    title="Volteyr API",
    description="Product enrichment search API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://localhost:8000",
        "http://127.0.0.1:8501",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(search_router)
app.include_router(meta_router)
