from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel

CATEGORIES = ["pro", "perso"]
PRIORITIES = ["P0", "P1", "P2"]
HORIZONS = ["court", "moyen", "long"]
STATUSES = ["active", "paused", "done", "dropped"]


class Objective(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    category: str = Field(index=True)
    priority: str = Field(default="P1", index=True)
    horizon: str = Field(default="moyen")
    status: str = Field(default="active", index=True)
    deadline: Optional[date] = None
    kpi: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


def validate_objective_fields(
    category: str,
    priority: str,
    horizon: str,
    status: str,
) -> list[str]:
    errors: list[str] = []
    if category not in CATEGORIES:
        errors.append(f"category must be one of {CATEGORIES}, got {category!r}")
    if priority not in PRIORITIES:
        errors.append(f"priority must be one of {PRIORITIES}, got {priority!r}")
    if horizon not in HORIZONS:
        errors.append(f"horizon must be one of {HORIZONS}, got {horizon!r}")
    if status not in STATUSES:
        errors.append(f"status must be one of {STATUSES}, got {status!r}")
    return errors
