from datetime import date, time

from app.domain.entities.birth_data import BirthData
from app.services.conception_service import ConceptionService


class TestConceptionService:
    """Тесты детерминированной генерации conception_time (Conception time derivation tests)."""

    def test_derive_returns_deterministic_result(self):
        """Одинаковые входные данные — одинаковый результат (Same input → same output)."""
        birth_data = BirthData(
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
        )
        dt1 = ConceptionService.derive(tg_id=12345, birth_data=birth_data)
        dt2 = ConceptionService.derive(tg_id=12345, birth_data=birth_data)
        assert dt1 == dt2

    def test_derive_different_users_different_result(self):
        """Разные пользователи — разный результат (Different users → different output)."""
        birth_data = BirthData(
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
        )
        dt1 = ConceptionService.derive(tg_id=12345, birth_data=birth_data)
        dt2 = ConceptionService.derive(tg_id=67890, birth_data=birth_data)
        assert dt1 != dt2

    def test_derive_result_is_before_birth(self):
        """Conception_time всегда раньше даты рождения (Conception is always before birth)."""
        birth_data = BirthData(
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
        )
        dt = ConceptionService.derive(tg_id=12345, birth_data=birth_data)
        assert dt.date() < birth_data.birth_date

    def test_derive_with_birth_time(self):
        """Учёт времени рождения (Birth time is factored in)."""
        birth_data1 = BirthData(
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
        )
        birth_data2 = BirthData(
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
            birth_time=time(14, 30),
        )
        dt1 = ConceptionService.derive(tg_id=12345, birth_data=birth_data1)
        dt2 = ConceptionService.derive(tg_id=12345, birth_data=birth_data2)
        assert dt1 != dt2

    def test_derive_with_parents_data(self):
        """Учёт данных родителей (Parents data is factored in)."""
        from app.domain.entities.birth_data import ParentData

        parent = ParentData(relation="mother", birth_date=date(1965, 3, 10))
        birth_data = BirthData(
            birth_date=date(1990, 5, 15),
            birth_place="Москва",
            parents=[parent],
        )
        dt = ConceptionService.derive(tg_id=12345, birth_data=birth_data)
        assert dt is not None
        assert dt.date() < birth_data.birth_date
