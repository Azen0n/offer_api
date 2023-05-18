import time

from fastapi import APIRouter, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from routers.utils import get_task_result_or_timeout
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
    offers, error = get_task_result_or_timeout(get_offers_task)
    if offers is None:
        raise HTTPException(**error)
    return offers


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
    offer, error = get_task_result_or_timeout(create_offer_task, offer)
    if offer is None:
        raise HTTPException(**error)
    return offer


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
    updated_offer, error = get_task_result_or_timeout(
        update_offer_task,
        offer_id,
        offer
    )
    if updated_offer is None:
        raise HTTPException(**error)
    return updated_offer
