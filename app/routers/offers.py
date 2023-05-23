import logging
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from routers.utils import get_task_result_or_timeout
from schemas import Offer
from schemas.offer import WriteOffer
from tasks.offer_tasks import (
    get_offers_task, create_offer_task, update_offer_task
)
from utils import get_environment_variable

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_PAGE_SIZE = int(get_environment_variable('DEFAULT_PAGE_SIZE'))


@router.get(
    '/',
    status_code=HTTP_200_OK,
    response_model=list[Offer]
)
async def get_offers(
        products_page_number: Annotated[int, Query(
            description='Страница списка подходящих товаров',
            gt=0
        )] = 1,
        products_page_size: Annotated[int, Query(
            description='Количество товаров на странице в списке подходящих товаров',
            gt=0
        )] = DEFAULT_PAGE_SIZE
):
    """Получение списка активных акций."""
    logger.info(f'Поступил запрос на {get_offers.__name__},'
                f' {products_page_number=}, {products_page_size=}')
    offers, error = get_task_result_or_timeout(
        get_offers_task,
        products_page_number,
        products_page_size
    )
    if offers is None:
        logger.error(f'Ошибка: {error["detail"]}')
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
    logger.info(f'Поступил запрос на {create_offer.__name__}, {offer=}')
    offer = jsonable_encoder(offer)
    offer, error = get_task_result_or_timeout(create_offer_task, offer)
    if offer is None:
        logger.error(f'Ошибка: {error["detail"]}')
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
    logger.info(f'Поступил запрос на {update_offer.__name__}, {offer_id=}, {offer=}')
    offer = jsonable_encoder(offer)
    updated_offer, error = get_task_result_or_timeout(
        update_offer_task,
        offer_id,
        offer
    )
    if updated_offer is None:
        logger.error(f'Ошибка: {error["detail"]}')
        raise HTTPException(**error)
    return updated_offer
