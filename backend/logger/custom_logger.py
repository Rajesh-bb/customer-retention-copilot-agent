import logging
import os
from datetime import datetime


os.makedirs("logs",exist_ok=True)

filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
logger = logging.getLogger(__name__)

logger.setLevel(logging.INFO)
formatter = logging.Formatter( "%(asctime)s | %(levelname)s | %(message)s")

file_handler = logging.FileHandler(f"logs/{filename}")
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

logger.propagate = False







