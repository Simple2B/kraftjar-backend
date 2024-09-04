import json
from enum import Enum
from config import config

CFG = config()


class Language(Enum):
    UA = CFG.UA
    EN = CFG.EN


class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return json.JSONEncoder.default(self, obj)
