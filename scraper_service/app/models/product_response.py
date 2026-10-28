from pydantic import BaseModel
from typing import Optional


class SizeVariant(BaseModel):
    size: str
    pid: str
    available: bool
    price: Optional[float] = None


class ColorVariant(BaseModel):
    color: str
    pid: str
    sizes: list[SizeVariant]


class ProductResponse(BaseModel):
    title: str
    brand: Optional[str] = None
    colors: list[ColorVariant]