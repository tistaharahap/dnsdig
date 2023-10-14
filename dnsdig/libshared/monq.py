from typing import TypeVar, Any, Dict, List, Type, Tuple

from beanie import Document
from pydantic import BaseModel
from pymongo import ReturnDocument
from pymongo.collation import Collation

T = TypeVar("T", bound=BaseModel)
TD = TypeVar("TD", bound=Document)


async def monq_find_many(
    model: Type[TD],
    query: Dict[str, Any],
    *,
    project_to: Type[T] | None = None,
    skip: int = 0,
    limit: int = 0,
    sort: List[Tuple[str, int]] | None = None,
    collation: Dict[str, Any] | Collation = None,
) -> List[T] | List[Dict] | List:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    if not collation:
        _cursor = coll.find(query, skip=skip, limit=limit, sort=sort)
    else:
        _cursor = coll.find(query, skip=skip, limit=limit, sort=sort).collation(collation)

    results = []
    async for doc in _cursor:
        results.append(doc)

    if not results or len(results) == 0:
        return []

    if not project_to:
        return results

    return [project_to(**result) for result in results]


async def monq_find_one(
    model: Type[TD],
    query: Dict[str, Any],
    *,
    project_to: Type[T] | None = None,
    collation: Dict[str, Any] | Collation = None,
) -> T | Dict | None:
    results = await monq_find_many(model=model, query=query, project_to=project_to, limit=1, collation=collation)
    if len(results) == 0:
        return None
    return results[0]


async def monq_delete_one(model: Type[TD], where: Dict[str, Any]) -> int:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    result = await coll.delete_one(where)

    return result.deleted_count


async def monq_lock_document(model: Type[TD], where: Dict[str, Any], lock_field: str) -> bool:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    result = await coll.find_one_and_update(where, {'$set': {lock_field: True}}, return_document=ReturnDocument.AFTER)

    return result is not None


async def monq_delete_many(model: Type[TD], where: Dict[str, Any]) -> int:
    coll = model.get_settings().motor_db[model.get_settings().name]
    if coll is None:
        raise EnvironmentError(f'Uninitialized collection: {model.Settings.name}')

    result = await coll.delete_many(where)

    return result.deleted_count
