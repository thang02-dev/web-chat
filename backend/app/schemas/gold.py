from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


class GoldPriceDto(BaseModel):
    gold_type: str
    buy_price: Decimal
    sell_price: Decimal
    price_date: Optional[str] = None


class GoldCardViewModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    gold_type: str
    buy_price: float
    sell_price: float
    price_date: Optional[str] = None
    updated_at: Optional[datetime] = None
    buy_price_delta: Optional[float] = None
    sell_price_delta: Optional[float] = None

    @computed_field
    @property
    def spread(self) -> float:
        """Chênh lệch giữa Giá Bán Ra và Giá Mua Vào (Bán - Mua)"""
        return abs(self.sell_price - self.buy_price)


class GoldBatchViewModel(BaseModel):
    batch_time: Optional[datetime] = None
    formatted_batch_time: str
    is_latest: bool
    cards: List[GoldCardViewModel] = Field(default_factory=list)


class CrawlResult(BaseModel):
    saved: int
    message: str


class VersionResponse(BaseModel):
    latest_time: int
