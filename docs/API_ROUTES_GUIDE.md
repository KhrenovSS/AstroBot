# Руководство по созданию API endpoints (Admin API)

> Шаблоны и примеры для FastAPI роутов админ-панели.

## Содержание

1. [Базовый шаблон](#1-базовый-шаблон)
2. [GET — список/статистика](#2-get--списокстатистика)
3. [GET — детальная информация](#3-get--детальная-информация)
4. [POST — действие/рассылка](#4-post--действиерассылка)
5. [Безопасность и auth](#5-безопасность-и-auth)
6. [Частые ошибки](#6-частые-ошибки)

---

## 1. Базовый шаблон

```python
# admin/routers/<domain>.py
from fastapi import APIRouter, Depends, status
from app.di import get_admin_service
from app.services.admin_stats_service import AdminStatsService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get("/stats")
async def get_stats(
    service: AdminStatsService = Depends(get_admin_service),
):
    """Получить статистику (Get admin statistics)"""
    stats = await service.get_stats()
    return stats
```

## 2. GET — список/статистика

```python
@router.get("/users")
async def list_users(
    page: int = 1,
    page_size: int = 20,
    service: AdminStatsService = Depends(get_admin_service),
):
    """Список пользователей (List users)"""
    users, total = await service.list_users(page=page, page_size=page_size)
    return {"users": users, "total": total, "page": page}
```

## 3. GET — детальная информация

```python
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    service: AdminStatsService = Depends(get_admin_service),
):
    """Детальная информация о пользователе (Get user details)"""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # НЕ возвращаем encrypted_birth_data
    return user.to_admin_dict()  # без ПДн
```

## 4. POST — действие/рассылка

```python
from pydantic import BaseModel

class BroadcastRequest(BaseModel):
    message: str
    target: str = "all"  # "all" | "active" | "paid"

@router.post("/broadcast")
async def broadcast(
    req: BroadcastRequest,
    service: AdminStatsService = Depends(get_admin_service),
):
    """Рассылка уведомлений пользователям (Broadcast notification)"""
    sent = await service.broadcast(message=req.message, target=req.target)
    return {"sent": sent, "status": "queued"}
```

## 5. Безопасность и auth

```python
# admin/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-Admin-Key")

async def verify_admin_key(x_admin_key: str = Depends(API_KEY_HEADER)):
    """Проверка API-ключа админки (Verify admin API key)"""
    from app.config import settings
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return True

# Использование
@router.get("/stats", dependencies=[Depends(verify_admin_key)])
async def get_stats(...):
    ...
```

## 6. Частые ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| 405 Method Not Allowed | Используется `@router.get` вместо `@router.post` | Проверить декоратор |
| PII в ответе | `User.__dict__` содержит `encrypted_birth_data` | Использовать `to_admin_dict()` |
| Нет верификации webhook | Платёжный webhook не проверяет подпись | Всегда вызывать `PaymentProvider.verify_webhook()` перед обработкой |
| Неправильный dependency | `Depends(get_admin_service)` а не `Depends(get_service)` | Для админ-роутов — только админские зависимости |

---

*Последнее обновление: 04.07.2026*
