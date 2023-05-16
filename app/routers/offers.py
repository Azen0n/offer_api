from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_404_NOT_FOUND

from auth import get_api_key
from schemas import Offer
from tasks.offer_tasks import (
    get_offers_task, create_offer_task, update_offer_task
)

router = APIRouter(
    tags=['offers'],
    prefix='/offers',
    dependencies=[Depends(get_api_key)]
)


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
        offer: Offer = Body(...)
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
        offer: Offer = Body(...)
):
    """Изменение акции."""
    offer = jsonable_encoder(offer)
    task = update_offer_task.delay(offer_id, offer)
    updated_offer = task.get()
    if updated_offer == HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail='Акция не найдена'
        )
    return updated_offer
