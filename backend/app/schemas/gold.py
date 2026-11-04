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


class DeleteBatchRequest(BaseModel):
    ids: List[int] = Field(default_factory=list, description="Danh sách ID bản ghi cần xóa")


class DeleteBatchResult(BaseModel):
    deleted: int
    message: str


class CrawlerConfigUpdate(BaseModel):
    interval_minutes: int = Field(10, ge=1, le=1440, description="Chu kỳ quét giá vàng tính theo phút (1 - 1440)")
    is_enabled: bool = Field(True, description="Trạng thái kích hoạt tự động quét")


class CrawlerLogItem(BaseModel):
    id: str
    timestamp: str
    source: str
    status: str
    saved_count: int
    message: str
    duration_ms: int


class CrawlerConfigResponse(BaseModel):
    interval_minutes: int
    is_enabled: bool
    is_crawling: bool
    last_crawl_at: Optional[str] = None
    last_crawl_status: str
    last_crawl_count: int
    last_crawl_message: str
    next_crawl_at: Optional[str] = None
    recent_logs: List[CrawlerLogItem] = Field(default_factory=list)


