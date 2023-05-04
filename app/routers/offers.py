from fastapi import APIRouter, Body, Request, status, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.openapi.models import APIKey

from auth import get_api_key
from schemas import Offer
from tasks.offer_tasks import get_offers_task, create_offer_task, update_offer_task

router = APIRouter()


@router.get('/', status_code=status.HTTP_200_OK, response_model=list[Offer])
async def get_offers(
        request: Request,
        api_key: APIKey = Depends(get_api_key)
):
    """Получение списка активных акций."""
    task = get_offers_task.delay()
    return task.get()


@router.post('/', status_code=status.HTTP_201_CREATED, response_model=Offer)
async def create_offer(
        request: Request,
        offer: Offer = Body(...),
        api_key: APIKey = Depends(get_api_key)
):
    """Добавление акции."""
    offer = jsonable_encoder(offer)
    task = create_offer_task.delay(offer)
    return task.get()


@router.put('/{offer_id}', status_code=status.HTTP_200_OK, response_model=Offer)
async def update_offer(
        request: Request,
        offer_id: str,
        offer: Offer = Body(...),
        api_key: APIKey = Depends(get_api_key)
):
    """Изменение акции."""
    offer = jsonable_encoder(offer)
    task = update_offer_task.delay(offer_id, offer)
    return task.get()
