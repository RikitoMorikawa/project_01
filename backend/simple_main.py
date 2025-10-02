from fastapi import FastAPI

app = FastAPI(
    title="CSR Lambda API System",
    version="1.0.0",
    description="Simple FastAPI for testing"
)

@app.get("/")
async def root():
    return {
        "message": "CSR Lambda API is running",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "message": "API is running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)