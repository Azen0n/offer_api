from database import db


def offers_exists(offer_ids: list[str]) -> bool:
    """Возвращает True, если все акции с указанными Id существуют."""
    offers = list(db['offers'].find({'_id': {'$in': offer_ids}}))
    offers_found = {offer['_id'] for offer in offers}
    return set(offer_ids) == offers_found


def product_exists(product_id: int) -> bool:
    """Возвращает True, если товар с указанным Id существует."""
    return db['products'].find_one({'_id': product_id}) is not None


def sale_exists(sale_id: int) -> bool:
    """Возвращает True, если продажа с указанным Id существует."""
    return db['sales'].find_one({'_id': sale_id}) is not None
