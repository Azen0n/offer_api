import datetime

from bson import ObjectId
from pymongo.client_session import ClientSession
from pymongo.database import Database
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from schemas import ApprovalProcessStatus
from schemas.offer import OfferStatus
from schemas.product import ProductStatus


def offers_exists(db: Database, offer_ids: list[ObjectId]) -> bool:
    """Возвращает True, если все акции с указанными Id существуют."""
    offers = list(db['offers'].find({'_id': {'$in': offer_ids}}))
    offers_found = {ObjectId(offer['_id']) for offer in offers}
    return set(offer_ids) == offers_found


def product_exists(db: Database, product_id: int) -> bool:
    """Возвращает True, если товар с указанным Id существует."""
    return db['products'].find_one({'id': product_id}) is not None


def sale_exists(db: Database, sale_id: int) -> bool:
    """Возвращает True, если продажа с указанным Id существует."""
    return db['sales'].find_one({'id': sale_id}) is not None


def find_compatible_products(db: Database) -> list[dict]:
    """Возвращает совместимые по параметрам товары."""
    compatible_products = list(db['products'].find({
        'status': ProductStatus.AVAILABLE.value
    }))
    compatible_products = [{'id': product['id'], 'status': product['status']}
                           for product in compatible_products]
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
                {'$set': {'status': OfferStatus.INACTIVE.value,
                          'end_date': datetime.datetime.now()}},
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
        offer = db['offers'].find_one({'_id': offer['_id']})
        if offer is None:
            return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                    'detail': 'Одна или более акции не существуют'}
        number_of_applications = get_offer_number_of_applications(db, offer['_id'])
        if number_of_applications < offer['application_limit']:
            db['offers'].find_one_and_update(
                {'_id': offer['_id']},
                {'$set': {'status': OfferStatus.ACTIVE.value,
                          'end_date': None}},
                session=session
            )


def get_offer_number_of_applications(db: Database, offer_id: ObjectId) -> int:
    """Возвращает количество применений акции."""
    number_of_applications = db['approval_processes'].count_documents({
        'status': ApprovalProcessStatus.APPROVED.value,
        'offers': {'_id': offer_id}
    })
    return number_of_applications


def change_approval_process_offers_status(
        db: Database,
        session: ClientSession,
        approval_process: dict,
        approval_process_status: str
) -> dict | None:
    """В зависимости от нового статуса процесса согласования
    изменяет статусы его акций.
    """
    error = None
    if approval_process_status == ApprovalProcessStatus.APPROVED.value:
        error = change_limit_reached_offers_status_to_inactive(
            db,
            session,
            approval_process['offers']
        )
    elif is_approved_status_changed(approval_process, approval_process_status):
        error = change_inactive_offers_status_to_active(
            db,
            session,
            approval_process['offers']
        )
    return error


def is_approved_status_changed(
        approval_process: dict,
        new_approval_process_status: str
) -> bool:
    """Возвращает True, если текущий статус "Одобрен" меняется на другой."""
    is_status_approved = approval_process['status'] == ApprovalProcessStatus.APPROVED.value
    is_new_status_not_approved = new_approval_process_status in [
        ApprovalProcessStatus.PENDING.value,
        ApprovalProcessStatus.CANCELLED.value,
        ApprovalProcessStatus.REJECTED.value
    ]
    return is_status_approved and is_new_status_not_approved


def convert_offer_dates_to_datetime(offer: dict):
    """Переводит start_date и end_time акции в объект datetime."""
    date_format = '%Y-%m-%dT%H:%M:%S'
    offer['start_date'] = datetime.datetime.strptime(
        offer['start_date'],
        date_format
    )
    if offer['end_date'] is not None:
        offer['end_date'] = datetime.datetime.strptime(
            offer['end_date'],
            date_format
        )
