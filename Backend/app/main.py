from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes.project_routes import project_router
from app.api.v1.routes.parse_routes import parse_router
from app.api.v1.routes.review_routes import review_router

app = FastAPI(title="AI Code Review System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project_router, prefix="/api/v1", tags=["projects"])
app.include_router(parse_router, prefix="/api/v1", tags=["parse"])
app.include_router(review_router, prefix="/api/v1", tags=["review"])

@app.get("/")
def home():
    return {"message": "AI Code Review System Running"}

@app.get("/health")
def health():
    return {"status": "ok"}