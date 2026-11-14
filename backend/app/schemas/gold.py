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
    notify_user_id: Optional[str] = Field(None, description="ID tài khoản nhận tin nhắn lịch sử call (None hoặc rỗng nếu tắt)")
    notify_mode: str = Field("ALWAYS", pattern=r"^(ALWAYS|CHANGE_ONLY)$", description="ALWAYS: Mỗi lần call | CHANGE_ONLY: Chỉ khi giá thay đổi")
    delete_changed_messages: bool = Field(
        False,
        description="False (Mặc định): Chỉ xóa tin nhắn giá vàng không thay đổi | True: Xóa cả tin nhắn giá vàng có thay đổi"
    )


class CrawlerCleanupRequest(BaseModel):
    delete_changed_messages: Optional[bool] = Field(
        None,
        description="Nếu truyền vào sẽ ghi đè chế độ xóa (False: chỉ xóa tin không đổi, True: xóa cả tin có thay đổi)"
    )


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
    notify_user_id: Optional[str] = None
    notify_mode: str = "ALWAYS"
    delete_changed_messages: bool = False
    sender_username: str = "admin"
    last_cleanup_date: Optional[str] = None
    bot_message_count: int = 0
    bot_unchanged_message_count: int = 0
    bot_changed_message_count: int = 0
    recent_logs: List[CrawlerLogItem] = Field(default_factory=list)


