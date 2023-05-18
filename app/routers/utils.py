import time
from typing import Any

from fastapi import HTTPException
from starlette.status import HTTP_408_REQUEST_TIMEOUT

from utils import get_environment_variable

TIMEOUT_SECONDS = int(get_environment_variable('TIMEOUT_SECONDS'))


def get_task_result_or_timeout(celery_task, *args) -> tuple[Any, dict]:
    """Запускает задачу и в течение 30 секунд ожидает результат.
    Если результат не пришел, возвращает ошибку с кодом 408.
    """
    task = celery_task.delay(*args)
    timeout_seconds_left = TIMEOUT_SECONDS
    while timeout_seconds_left > 0:
        if task.ready():
            return task.get()
        time.sleep(1)
        timeout_seconds_left -= 1
    raise HTTPException(status_code=HTTP_408_REQUEST_TIMEOUT,
                        detail='Превышено время ожидания')
