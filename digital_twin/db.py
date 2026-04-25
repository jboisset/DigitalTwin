from datetime import date, datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine, select

from .models import Objective, validate_objective_fields

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "twin.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(_engine)


def get_session() -> Session:
    return Session(_engine)


def list_objectives(
    category: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
) -> list[Objective]:
    with get_session() as s:
        q = select(Objective)
        if category:
            q = q.where(Objective.category == category)
        if status:
            q = q.where(Objective.status == status)
        if priority:
            q = q.where(Objective.priority == priority)
        q = q.order_by(Objective.priority, Objective.category, Objective.id)
        return list(s.exec(q).all())


def get_objective(objective_id: int) -> Optional[Objective]:
    with get_session() as s:
        return s.get(Objective, objective_id)


def upsert_objective(
    *,
    id: Optional[int] = None,
    title: str,
    description: Optional[str] = None,
    category: str,
    priority: str = "P1",
    horizon: str = "moyen",
    status: str = "active",
    deadline: Optional[date] = None,
    kpi: Optional[str] = None,
) -> Objective:
    errors = validate_objective_fields(category, priority, horizon, status)
    if errors:
        raise ValueError("; ".join(errors))

    with get_session() as s:
        if id is not None:
            obj = s.get(Objective, id)
            if obj is None:
                raise ValueError(f"Objective id={id} not found")
            obj.title = title
            obj.description = description
            obj.category = category
            obj.priority = priority
            obj.horizon = horizon
            obj.status = status
            obj.deadline = deadline
            obj.kpi = kpi
            obj.updated_at = datetime.utcnow()
        else:
            obj = Objective(
                title=title,
                description=description,
                category=category,
                priority=priority,
                horizon=horizon,
                status=status,
                deadline=deadline,
                kpi=kpi,
            )
            s.add(obj)
        s.commit()
        s.refresh(obj)
        return obj


def delete_objective(objective_id: int) -> bool:
    with get_session() as s:
        obj = s.get(Objective, objective_id)
        if obj is None:
            return False
        s.delete(obj)
        s.commit()
        return True
