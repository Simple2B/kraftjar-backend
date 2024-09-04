from enum import Enum
from config import config

CFG = config()


class Language(Enum):
    UA = CFG.UA
    EN = CFG.EN
