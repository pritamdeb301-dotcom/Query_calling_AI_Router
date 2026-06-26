"""FastAPI application entry‑point for the Doctor Appointment Booking AI.

The server wires together:
* Database session handling (SQLModel via SQLite)
* RAG vector store initialization (Chroma)
* API routers for call triggering, voice queries, slot checking, and booking
* Simple health‑check endpoint
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import Settings
from app.rag.vectorstore import get_vectorstore
from sqlmodel import SQLModel
from app.database.session import engine
import app.database.models as models  # This forces Python to register your tables
# Import routers – they are defined in ``app/api/routes``
from app.api.routes.trigger_call import router as trigger_router
from app.api.routes.voice_query import router as voice_query_router
from app.api.routes.availability import router as availability_router
from app.api.routes.booking import router as booking_router

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------
settings = Settings()
logging.basicConfig(level=logging.INFO if settings.debug else logging.WARNING)
logger = logging.getLogger("appointment_ai")

app = FastAPI(
    title="Appointment Booking AI",
    version="1.0",
    description="FastAPI backend powering a voice‑AI receptionist for Dr. Pratik Mozumder clinic.",
)

# Enable CORS for any origin – adjust in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup / shutdown events
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info("Initializing database tables...")
    # This line automatically creates appointments.db tables if they are missing
    SQLModel.metadata.create_all(engine)
    
    logger.info("Initializing vector store on startup...")
    # ... (keep whatever your existing vector store code was below this) ...

# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(trigger_router, prefix="/api", tags=["Public"])
app.include_router(voice_query_router, prefix="/api/webhook", tags=["Webhook"])
app.include_router(availability_router, prefix="/api/webhook", tags=["Webhook"])
app.include_router(booking_router, prefix="/api/webhook", tags=["Webhook"])

# ---------------------------------------------------------------------------
# Simple health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ---------------------------------------------------------------------------
# Optional: expose the vectorstore for debugging (not part of public API)
# ---------------------------------------------------------------------------
# from fastapi import Depends
# @app.get("/debug/vector-count")
# async def vector_count():
#     store = get_vectorstore()
#     col = store.get_or_create_collection()
#     return {"num_documents": col.count()}
