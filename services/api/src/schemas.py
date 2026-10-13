"""Shared schemas — APIResponse envelope.
Mirrors the analyzed backend family's contract: every endpoint returns
{status_code, message, data, metadata}. Frontends unwrap `data`.
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    status_code: int = 200
    message: str = "ok"
    data: T | None = None
    metadata: dict | None = None


def ok(data: T, message: str = "ok") -> APIResponse[T]:
    return APIResponse(status_code=200, message=message, data=data)
