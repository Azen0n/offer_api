from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from schemas import Offer
from schemas.offer import WriteOffer
from tasks.offer_tasks import (
    get_offers_task, create_offer_task, update_offer_task
)

router = APIRouter()


@router.get(
    '/',
    status_code=HTTP_200_OK,
    response_model=list[Offer]
)
async def get_offers():
    """Получение списка активных акций."""
    task = get_offers_task.delay()
    return task.get()


@router.post(
    '/',
    status_code=HTTP_201_CREATED,
    response_model=Offer
)
async def create_offer(
        offer: WriteOffer = Body(...)
):
    """Добавление акции."""
    offer = jsonable_encoder(offer)
    task = create_offer_task.delay(offer)
    return task.get()


@router.put(
    '/{offer_id}',
    status_code=HTTP_200_OK,
    response_model=Offer
)
async def update_offer(
        offer_id: str,
        offer: WriteOffer = Body(...)
):
    """Изменение акции."""
    offer = jsonable_encoder(offer)
    task = update_offer_task.delay(offer_id, offer)
    updated_offer, error = task.get()
    if updated_offer is None:
        raise HTTPException(**error)
    return updated_offer
