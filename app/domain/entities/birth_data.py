from datetime import date, time

from pydantic import BaseModel


class ParentData(BaseModel):
    """Даты рождения родителей (Parent birth dates)."""
    relation: str  # mother / father
    birth_date: date
    birth_time: time | None = None


class BirthData(BaseModel):
    """Собранные ПДн для расчёта времени зачатия (Collected PII for conception calculation)."""
    birth_date: date
    birth_place: str
    birth_time: time | None = None
    parents: list[ParentData] = []
