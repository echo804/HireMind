"""Unified API Response"""

from typing import Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class Result(BaseModel, Generic[T]):
    """Unified API response wrapper"""
    code: int = 0
    message: str = "success"
    data: T | None = None

    @staticmethod
    def success(data: T = None) -> "Result[T]":
        return Result(code=0, message="success", data=data)

    @staticmethod
    def error(code: int, message: str) -> "Result":
        return Result(code=code, message=message, data=None)
