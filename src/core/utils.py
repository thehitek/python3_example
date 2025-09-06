from datetime import datetime
from enum import Enum
from typing import Sequence
from fastapi import HTTPException

from passlib.context import CryptContext

from src.core.config import HASHING_SETTINGS, TIMEZONE

pwd_context = CryptContext(
    schemes=[HASHING_SETTINGS.algorithm],
    deprecated="auto",
    bcrypt__rounds=HASHING_SETTINGS.iterations,
)


def verify_password(password: str, hashed_password: bytes) -> bool:
    return pwd_context.verify(password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def datetime_now(fix_tz: bool = True) -> datetime:
    result = datetime.now(TIMEZONE) if fix_tz else datetime.now()
    return result


def get_res_from_exc(exc: Sequence[HTTPException]):
    return {e.status_code: {"detail": e.detail} for e in exc}

# определяем класс, от которого можно наследоваться при создании enum
# при установлении в поле значение enum.auto(), будет использоваться его название,
# т.е foo = enum.auto() -> foo.name = foo.value = foo
class AutoNameEnum(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name
    
def to_datetime(value):
    match type(value).__qualname__:
        case str.__qualname__: return datetime.fromisoformat(value)
        case datetime.__qualname__: return value
        case _: return None
        