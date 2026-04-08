from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api import routes
from app.db.database import Base, engine

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Complaint Prioritization AI",
    description="Context-aware complaint prioritization with explainable reasoning",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router)

# Serve static files (dashboard.html)
app.mount("/static", StaticFiles(directory="."), name="static")


@app.get("/dashboard-page")
def get_dashboard_page():
    """Serve the HTML dashboard page."""
    return FileResponse("dashboard.html", media_type="text/html")


@app.get("/")
def root():
    return {"status": "Complaint priorization AI is up", "dashboard": "/dashboard-page"}
