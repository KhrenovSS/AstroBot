import hashlib
import struct
from datetime import datetime, timedelta, timezone

from app.domain.entities.birth_data import BirthData


class ConceptionService:
    """Детерминированная генерация времени зачатия (Deterministic conception time).

    Seed = hash(tg_id + birth_date + birth_place + ...) → reproducible.
    """

    # Диапазон дней до рождения для генерации conception_time
    MIN_DAYS_BEFORE_BIRTH = 266  # ~38 недель (доношенная беременность)
    MAX_DAYS_BEFORE_BIRTH = 287  # ~41 неделя

    OFFSET_SECONDS_RANGE = (MAX_DAYS_BEFORE_BIRTH - MIN_DAYS_BEFORE_BIRTH) * 86400

    @staticmethod
    def derive(tg_id: int, birth_data: BirthData) -> datetime:
        """Вычислить детерминированное время зачатия (Derive deterministic conception datetime).

        Возвращает datetime в UTC.
        """
        # Сбор seed-строки из всех доступных данных (Seed string from all available data)
        seed_parts = [
            str(tg_id),
            birth_data.birth_date.isoformat(),
            birth_data.birth_place,
        ]

        if birth_data.birth_time:
            seed_parts.append(birth_data.birth_time.isoformat())

        for parent in birth_data.parents:
            seed_parts.append(parent.relation)
            seed_parts.append(parent.birth_date.isoformat())
            if parent.birth_time:
                seed_parts.append(parent.birth_time.isoformat())

        seed_str = "|".join(seed_parts)

        # Хеш → 64-битное целое (Hash → 64-bit integer)
        digest = hashlib.sha256(seed_str.encode("utf-8")).digest()
        (seed_int,) = struct.unpack("!Q", digest[:8])

        # Псевдослучайное смещение от MIN_DAYS_BEFORE_BIRTH (Random offset within range)
        offset_seconds = seed_int % ConceptionService.OFFSET_SECONDS_RANGE

        # Время зачатия = дата рождения - минимальный срок - случайное смещение
        # (Conception = birth date - min gestation - random offset)
        birth_dt = datetime.combine(
            birth_data.birth_date,
            birth_data.birth_time or datetime.min.time(),
            tzinfo=timezone.utc,
        )

        conception = birth_dt - timedelta(
            days=ConceptionService.MIN_DAYS_BEFORE_BIRTH,
            seconds=offset_seconds,
        )

        return conception
