import datetime

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.client_session import ClientSession
from pymongo.database import Database
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_404_NOT_FOUND

from schemas import ApprovalProcessStatus
from schemas.offer import OfferStatus
from schemas.product import ProductStatus


def validate_create_approval_process(db: Database, approval_process: dict) -> dict | None:
    """Проверяет, существуют ли процесс согласования или переданные
    товар, продажа и акции.

    Возвращает словарь с ошибкой, если проверка провалилась или None.
    """
    existing_approval_process = db['approval_processes'].find_one(
        {'sale.id': approval_process['sale']['id']}
    )
    if existing_approval_process is not None:
        return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': 'Процесс согласования продажи уже существует'}
    if not product_exists(db, approval_process['product']['id']):
        return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': 'Товар не найден'}
    if not sale_exists(db, approval_process['sale']['id']):
        return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': 'Продажа не найдена'}
    for offer in approval_process['offers']:
        offer['_id'] = ObjectId(offer['_id'])
    offer_ids = [offer['_id'] for offer in approval_process['offers']]
    if not offers_exists(db, offer_ids):
        return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': 'Одна или более акции не существуют'}
    return None


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


def get_offer_number_of_applications(db: Database, offer_id: ObjectId) -> int:
    """Возвращает количество применений акции."""
    number_of_applications = db['approval_processes'].count_documents({
        'status': ApprovalProcessStatus.APPROVED.value,
        'offers': {'_id': offer_id}
    })
    return number_of_applications


def update_approval_process_status(
        db: Database,
        session: ClientSession,
        approval_process: dict,
        new_status: str
):
    """Обновляет статус процесса согласования."""
    updated_approval_process = db['approval_processes'].find_one_and_update(
        {'_id': ObjectId(approval_process['_id'])},
        {'$set': {'status': new_status}},
        return_document=ReturnDocument.AFTER,
        session=session
    )
    return updated_approval_process


def change_approval_process_offers_status(
        db: Database,
        session: ClientSession,
        approval_process: dict,
        new_approval_process_status: str
) -> dict | None:
    """Изменяет статусы акций после изменения статуса процесса согласования:
    При изменении статуса на "Одобрен":
        Активные акции становится не активными, если с новым процессом
        согласования достигнут их лимит применений.
    При изменении статуса с "Одобрен" на любой другой:
        Не активные акции становятся активными, если без процесса согласования
        лимит применений не будет достигнут.

    Возвращает словарь с ошибкой или None.
    """
    error = None
    if new_approval_process_status == ApprovalProcessStatus.APPROVED.value:
        error = change_active_offers_status_to_inactive(
            db, session, approval_process['offers']
        )
    elif is_approved_status_changed(approval_process, new_approval_process_status):
        error = change_inactive_offers_status_to_active(
            db, session, approval_process['offers']
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


def change_active_offers_status_to_inactive(
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
    """Изменяет статус не активных акций на активный, если не превышен
    лимит применений. Если одна из акций не найдена, возвращает словарь с ошибкой.
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


def convert_approval_process_objectid_fields_to_str(approval_process: dict):
    """Приводит Id процесса согласования и Id акций (ObjectId) к str."""
    approval_process['_id'] = str(approval_process['_id'])
    convert_offers_objectid_fields_to_str(approval_process['offers'])


def convert_offers_objectid_fields_to_str(offers: list[dict]):
    """Приводит Id акций (ObjectId) к str."""
    for offer in offers:
        offer['_id'] = str(offer['_id'])


def validate_approval_process_exists(approval_process: dict) -> dict | None:
    """Проверяет, существует ли процесс согласования.

    Возвращает словарь с ошибкой, если проверка провалилась или None.
    """
    if approval_process is None:
        return {'status_code': HTTP_404_NOT_FOUND,
                'detail': 'Процесс согласования не найден'}
    return None


def validate_get_approval_process_offers(approval_process: dict) -> dict | None:
    """Проверяет, существует ли процесс согласования и зафиксирована ли
    (одобрена) продажа.

    Возвращает словарь с ошибкой, если проверка провалилась или None.
    """
    if approval_process is None:
        return {'status_code': HTTP_404_NOT_FOUND,
                'detail': 'Процесс согласования не найден'}
    if approval_process['status'] != ApprovalProcessStatus.APPROVED.value:
        return {'status_code': HTTP_422_UNPROCESSABLE_ENTITY,
                'detail': 'Продажа товара не зафиксирована'}
    return None


def get_offers_by_approval_process_offer_ids(
        db: Database,
        approval_process: dict,
        page_number: int,
        page_size: int
) -> list[dict]:
    """Возвращает список акций процесса согласования со всеми полями
    по Id акций из процесса согласования.
    """
    skip_value = (page_number - 1) * page_size
    offer_ids = [ObjectId(offer['_id']) for offer in approval_process['offers']]
    offers = list(db['offers'].find(
        {'_id': {'$in': offer_ids}},
        {'compatible_products': {'$slice': [skip_value, page_size]}}
    ))
    return offers
