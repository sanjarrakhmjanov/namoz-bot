import logging

from aiogram import Router

router = Router()
logger = logging.getLogger(__name__)


@router.errors()
async def errors_handler(event, exception=None):
    logger.exception("Unhandled exception: %s", exception or event)
    return True
