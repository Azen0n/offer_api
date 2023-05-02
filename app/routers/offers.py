from fastapi import APIRouter, Body, Request, status
from fastapi.encoders import jsonable_encoder
from pymongo import ReturnDocument

from schemas import Offer, OfferStatus

router = APIRouter()


@router.get(
    '/',
    response_model=list[Offer]
)
def get_offers(request: Request):
    """Получение списка активных акций."""
    offers = list(request.app.database['offers'].find({'status': OfferStatus.ACTIVE.value}))
    return offers


@router.post(
    '/',
    status_code=status.HTTP_201_CREATED,
    response_model=Offer
)
def create_offer(request: Request, offer: Offer = Body(...)):
    """Добавление акции."""
    offer = jsonable_encoder(offer)
    new_offer = request.app.database['offers'].insert_one(offer)
    created_offer = request.app.database['offers'].find_one(
        {'_id': new_offer.inserted_id}
    )
    return created_offer


@router.put(
    '/{offer_id}',
    status_code=status.HTTP_200_OK,
    response_model=Offer
)
def update_offer(request: Request, offer_id: str, offer: Offer = Body(...)):
    """Изменение акции."""
    updated_offer = request.app.database['offers'].find_one_and_update(
        {"_id": offer_id},
        {"$set": offer.dict()},
        return_document=ReturnDocument.AFTER
    )
    return updated_offer
