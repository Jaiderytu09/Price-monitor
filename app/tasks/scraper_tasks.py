import logging

from app.core.database import SessionLocal
from app.models.product import PriceHistory, Product
from app.scraper.extractor import fetch_price
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.scraper_tasks.check_product_price")
def check_product_price(product_id: int) -> dict:
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product or not product.is_active:
            return {"status": "skipped", "product_id": product_id}

        price = fetch_price(product.url)
        price_changed = product.current_price != price

        if price_changed:
            product.current_price = price
            history_entry = PriceHistory(product_id=product.id, price=price)
            db.add(history_entry)
            db.commit()

        alert_triggered = price <= product.target_price
        if alert_triggered and price_changed:
            logger.info(
                "Alerta de precio: %s bajó a %.2f (objetivo: %.2f)",
                product.name,
                price,
                product.target_price,
            )

        return {
            "status": "ok",
            "product_id": product.id,
            "price": price,
            "price_changed": price_changed,
            "alert_triggered": alert_triggered,
        }
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Error al revisar el precio del producto %s", product_id
        )
        return {
            "status": "error",
            "product_id": product_id,
            "detail": str(exc),
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.scraper_tasks.check_all_prices")
def check_all_prices() -> dict:
    db = SessionLocal()
    try:
        active_products = (
            db.query(Product.id).filter(Product.is_active.is_(True)).all()
        )
        product_ids = [row[0] for row in active_products]
        for product_id in product_ids:
            check_product_price.delay(product_id)

        return {"status": "queued", "count": len(product_ids)}
    finally:
        db.close()