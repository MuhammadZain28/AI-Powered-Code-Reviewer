from fastapi import FastAPI

app = FastAPI(title="AI Code Review System")

@app.get("/")
def home():
    return {"message": "AI Code Review System Running"}

@app.get("/health")
def health():
    return {"status": "ok"}