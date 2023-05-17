from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from utils import get_environment_variable

API_KEY_NAME = get_environment_variable('API_KEY_NAME')
API_KEY = get_environment_variable('API_KEY')
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


async def check_api_key(api_key: str = Security(api_key_header)) -> str:
    """Проверка ключа API из заголовка запроса."""
    if api_key == API_KEY:
        return api_key
    raise HTTPException(status_code=HTTP_403_FORBIDDEN)
