from celery import Celery

from utils import get_environment_variable

REDIS_BROKER_URL = get_environment_variable('REDIS_BROKER_URL')
REDIS_RESULT_BACKEND = get_environment_variable('REDIS_RESULT_BACKEND')

app = Celery('celery_app',
             broker=REDIS_BROKER_URL,
             backend=REDIS_RESULT_BACKEND,
             include=['tasks'])
