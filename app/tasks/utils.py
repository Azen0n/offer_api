from bson import ObjectId
from pymongo.database import Database

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
