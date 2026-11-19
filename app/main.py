from fastapi import FastAPI

app = FastAPI(
    title="Price Monitor API",
    description="API para monitoreo de precios y alertas automáticas",
    version="0.1.0",
)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "price-monitor"}