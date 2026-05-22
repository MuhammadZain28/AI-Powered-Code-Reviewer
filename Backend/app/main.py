from fastapi import FastAPI
from app.api.v1.routes.project_routes import project_router
from app.api.v1.routes.parse_routes import parse_router
app = FastAPI(title="AI Code Review System")

app.include_router(project_router, prefix="/api/v1", tags=["projects"])
app.include_router(parse_router, prefix="/api/v1", tags=["parse"])

@app.get("/")
def home():
    return {"message": "AI Code Review System Running"}

@app.get("/health")
def health():
    return {"status": "ok"}