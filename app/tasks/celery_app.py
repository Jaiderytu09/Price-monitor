from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "price_monitor",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.scraper_tasks"],
)

celery_app.conf.update(
    timezone="America/Bogota",
    enable_utc=True,
    beat_schedule={
        "check-all-product-prices": {
            "task": "app.tasks.scraper_tasks.check_all_prices",
            "schedule": 3600.0,
        },
    },
)