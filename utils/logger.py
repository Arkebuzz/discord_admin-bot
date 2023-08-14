import logging

from config import PATH_LOG

formatting = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler(PATH_LOG, mode='a')
file_handler.setFormatter(formatting)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatting)

logger = logging.getLogger('KBAHT')
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
