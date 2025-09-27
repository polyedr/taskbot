import logging
import os

from dotenv import load_dotenv

load_dotenv()

LOGGER = logging.getLogger("task-bot")
if not LOGGER.handlers:
    LOGGER.setLevel(logging.INFO)
    _h = logging.StreamHandler()
    _f = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    _h.setFormatter(_f)
    LOGGER.addHandler(_h)

BOT_TOKEN = os.getenv("BOT_TOKEN")
PG_DSN = os.getenv("PG_DSN")
ADMINS = os.getenv("ADMINS", "").split(",")
