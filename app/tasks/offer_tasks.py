from bson import ObjectId
from pymongo import ReturnDocument
from starlette.status import HTTP_404_NOT_FOUND

from celery_app import app
from schemas import OfferStatus

from database import db
from tasks.utils import find_compatible_products


@app.task(name='get_offers')
def get_offers_task() -> list[dict]:
    """Получение списка активных акций.

    Возвращает список Offer в виде словарей.
    """
    offers = list(db['offers'].find({'status': OfferStatus.ACTIVE.value}))
    for offer in offers:
        offer['_id'] = str(offer['_id'])
    return offers


@app.task(name='create_offer')
def create_offer_task(offer: dict) -> dict:
    """Добавление акции.

    Возвращает созданный Offer в виде словаря.
    """
    offer['compatible_products'] = find_compatible_products()
    new_offer = db['offers'].insert_one(offer)
    created_offer = db['offers'].find_one(
        {'_id': new_offer.inserted_id}
    )
    created_offer['_id'] = str(created_offer['_id'])
    return created_offer


@app.task(name='update_offer')
def update_offer_task(offer_id: str, offer: dict) -> tuple[dict | None, dict | None]:
    """Изменение акции.

    Возвращает Offer в виде словаря и словарь с кодом ошибки и описанием.
    При отсутствии один из элементов равен None.
    """
    offer['compatible_products'] = find_compatible_products()
    updated_offer = db['offers'].find_one_and_update(
        {'_id': ObjectId(offer_id)},
        {'$set': offer},
        return_document=ReturnDocument.AFTER
    )
    if updated_offer is None:
        return None, {'status_code': HTTP_404_NOT_FOUND,
                      'detail': 'Акция не найдена'}
    updated_offer['_id'] = str(updated_offer['_id'])
    return updated_offer, None
