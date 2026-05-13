from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator
from app.database import engine, Base
from app.routers import tasks

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TaskAPI", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

Instrumentator().instrument(app).expose(app)

app.mount("/ui", StaticFiles(directory="app/static", html=True), name="ui")

@app.get("/")
def root():
    return RedirectResponse(url="/ui")

@app.get("/health")
def health():
    return {"status": "ok"}
