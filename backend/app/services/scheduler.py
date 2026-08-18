import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.database import SessionLocal
from app.services.alerta_service import verificar_vencimentos_todas_empresas

logger = logging.getLogger("valistock")
settings = get_settings()


def executar_verificacao_de_vencimentos() -> None:
    db = SessionLocal()
    try:
        verificar_vencimentos_todas_empresas(db)
        logger.info("Verificacao diaria de vencimentos concluida.")
    except Exception:
        logger.exception("Falha ao executar a verificacao diaria de vencimentos.")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    """Creates and starts a fresh scheduler instance (APScheduler schedulers cannot be restarted after shutdown)."""
    scheduler = BackgroundScheduler(timezone=settings.timezone)
    # Roda uma vez ao iniciar (util em dev/demo) e depois todo dia as 06:00.
    executar_verificacao_de_vencimentos()
    scheduler.add_job(
        executar_verificacao_de_vencimentos,
        trigger=CronTrigger(hour=6, minute=0),
        id="verificacao_diaria_vencimentos",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler


def stop_scheduler(scheduler: BackgroundScheduler) -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
