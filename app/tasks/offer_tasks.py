from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import ConnectionFailure
from starlette.status import HTTP_404_NOT_FOUND

from celery_app import app
from schemas import OfferStatus

from database import MongoConnection, MONGODB_URL, MONGO_INITDB_DATABASE
from tasks.utils import find_compatible_products
from utils import get_environment_variable

DEFAULT_PAGE_SIZE = int(get_environment_variable('DEFAULT_PAGE_SIZE'))


@app.task(name='get_offers')
def get_offers_task(page_number: int, page_size: int) -> tuple[list[dict] | None, dict | None]:
    """Получение списка активных акций.

    Возвращает список Offer в виде словарей.
    """
    skip_value = (page_number - 1) * page_size
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            offers = list(mongo.db['offers'].find(
                {'status': OfferStatus.ACTIVE.value},
                {'compatible_products': {'$slice': [skip_value, page_size]}}
            ))
            for offer in offers:
                offer['_id'] = str(offer['_id'])
            return offers, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}


@app.task(name='create_offer')
def create_offer_task(offer: dict) -> tuple[dict | None, dict | None]:
    """Добавление акции.

    Возвращает созданный Offer в виде словаря.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            offer['compatible_products'] = find_compatible_products(mongo.db)
            new_offer = mongo.db['offers'].insert_one(offer)
            created_offer = mongo.db['offers'].find_one(
                {'_id': new_offer.inserted_id}
            )
            created_offer['_id'] = str(created_offer['_id'])
            created_offer['compatible_products'] = created_offer['compatible_products'][0:DEFAULT_PAGE_SIZE]
            return created_offer, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}


@app.task(name='update_offer')
def update_offer_task(offer_id: str, offer: dict) -> tuple[dict | None, dict | None]:
    """Изменение акции.

    Возвращает Offer в виде словаря и словарь с кодом ошибки и описанием.
    При отсутствии один из элементов равен None.
    """
    try:
        with MongoConnection(MONGODB_URL, MONGO_INITDB_DATABASE) as mongo:
            offer['compatible_products'] = find_compatible_products(mongo.db)
            updated_offer = mongo.db['offers'].find_one_and_update(
                {'_id': ObjectId(offer_id)},
                {'$set': offer},
                return_document=ReturnDocument.AFTER
            )
            if updated_offer is None:
                return None, {'status_code': HTTP_404_NOT_FOUND,
                              'detail': 'Акция не найдена'}
            updated_offer['_id'] = str(updated_offer['_id'])
            updated_offer['compatible_products'] = updated_offer['compatible_products'][0:DEFAULT_PAGE_SIZE]
            return updated_offer, None
    except ConnectionFailure as e:
        return None, {'status_code': 500, 'detail': f'{e}'}
