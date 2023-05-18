from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.database import Database
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from schemas import ApprovalProcessStatus
from schemas.offer import OfferId, OfferStatus
from schemas.product import Product


def offers_exists(db: Database, offer_ids: list[ObjectId]) -> bool:
    """Возвращает True, если все акции с указанными Id существуют."""
    offers = list(db['offers'].find({'_id': {'$in': offer_ids}}))
    offers_found = {ObjectId(offer['_id']) for offer in offers}
    return set(offer_ids) == offers_found


def product_exists(db: Database, product_id: int) -> bool:
    """Возвращает True, если товар с указанным Id существует."""
    return db['products'].find_one({'_id': product_id}) is not None


def sale_exists(db: Database, sale_id: int) -> bool:
    """Возвращает True, если продажа с указанным Id существует."""
    return db['sales'].find_one({'_id': sale_id}) is not None


def find_compatible_products() -> list[Product]:
    """Возвращает совместимые по параметрам товары."""
    compatible_products = []
    return compatible_products


def change_limit_reached_offers_status_to_inactive(
        db: Database,
        session: ClientSession,
        offers: list[dict]
) -> dict | None:
    """Изменяет статус акций на не активный, если достигнут лимит применений.
    Если одна из акций не найдена, возвращает словарь с ошибкой.
    """
    for offer in offers:
        offer = db['offers'].find_one({'_id': offer['_id']})
        if offer is None:
            return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                    'detail': 'Одна или более акции не существуют'}
        number_of_applications = get_offer_number_of_applications(db, offer['_id'])
        if number_of_applications >= offer['application_limit']:
            db['offers'].find_one_and_update(
                {'_id': offer['_id']},
                {'$set': {'status': OfferStatus.INACTIVE.value}},
                session=session
            )


def change_inactive_offers_status_to_active(
        db: Database,
        session: ClientSession,
        offers: list[dict]
) -> dict | None:
    """Изменяет статус не активных акций на активный.
    Если одна из акций не найдена, возвращает словарь с ошибкой.
    """
    for offer in offers:
        offer = db['offers'].find_one_and_update(
            {'_id': offer['_id']},
            {'$set': {'status': OfferStatus.ACTIVE.value}},
            session=session
        )
        if offer is None:
            return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                    'detail': 'Одна или более акции не существуют'}


def get_offer_number_of_applications(db: Database, offer_id: ObjectId) -> int:
    """Возвращает количество применений акции."""
    number_of_applications = db['approval_processes'].count_documents({
        'status': ApprovalProcessStatus.APPROVED.value,
        'offers': {'_id': offer_id}
    })
    return number_of_applications
