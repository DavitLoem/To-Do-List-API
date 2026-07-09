from fastapi import APIRouter, Body, HTTPException, Depends
from src.model.todo_model import CategoryItem, CategoryUpdate
from src.services.category_services import (
    create_category, get_categories, get_category_by_id,
    update_category, delete_category
)
from src.services.auth_services import get_current_user

category_router = APIRouter(prefix='/api/categories', tags=['Categories'])


def _serialize(category: dict) -> dict:
    category = dict(category)
    category['id'] = str(category.pop('_id'))
    return category


@category_router.post('/', summary='Create a category')
async def add_category(body: CategoryItem, user_id: str = Depends(get_current_user)):
    result = await create_category(user_id, body.model_dump())
    return {'message': 'Category created', 'id': str(result.inserted_id)}


@category_router.get('/', summary='List categories')
async def list_categories(user_id: str = Depends(get_current_user)):
    categories = await get_categories(user_id)
    return [_serialize(c) for c in categories]


@category_router.get('/{category_id}', summary='Get a single category')
async def get_category(category_id: str, user_id: str = Depends(get_current_user)):
    category = await get_category_by_id(category_id, user_id)
    if not category:
        raise HTTPException(status_code=404, detail='Category not found')
    return _serialize(category)


@category_router.put('/{category_id}', summary='Update a category')
async def edit_category(category_id: str, body: CategoryUpdate, user_id: str = Depends(get_current_user)):
    result = await update_category(category_id, user_id, body.model_dump(exclude_unset=True))
    if result is None or result.matched_count == 0:
        raise HTTPException(status_code=404, detail='Category not found')
    return {'message': 'Category updated'}


@category_router.delete('/{category_id}', summary='Delete a category')
async def remove_category(category_id: str, user_id: str = Depends(get_current_user)):
    result = await delete_category(category_id, user_id)
    if result is None or result.deleted_count == 0:
        raise HTTPException(status_code=404, detail='Category not found')
    return {'message': 'Category deleted'}
