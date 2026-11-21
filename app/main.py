from fastapi import FastAPI

from app.api.products import router as products_router

app = FastAPI(
    title="Price Monitor API",
    description="API para monitoreo de precios y alertas automáticas",
    version="0.1.0",
)

app.include_router(products_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "price-monitor"}