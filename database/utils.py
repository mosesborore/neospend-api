from typing import Any, Optional

from sqlmodel import select

from database.db import create_session


def get_or_create(entity: Any, filter_map: dict[str, Any], defaults: Optional[dict] = None):
    """
    :param entity: a mapped class indicating the
    type of entity to be loaded.

    :param filter_map: dict representing filtering criteria.
    :return: The `entity` instance and `created` if new entity was created
    """
    created = False

    with create_session() as session:
        statement = select(entity).filter_by(**filter_map)

        obj = session.exec(statement).first()
        if obj is None:
            obj = entity(**defaults)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            created = True

        return obj, created
