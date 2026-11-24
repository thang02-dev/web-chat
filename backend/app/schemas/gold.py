import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


class GoldPriceDto(BaseModel):
    gold_type: str
    buy_price: Decimal
    sell_price: Decimal
    price_date: Optional[str] = None


class ExtractRules(BaseModel):
    mode: Literal["AUTO", "CSS"] = "AUTO"
    price_url: Optional[str] = Field(None, max_length=2000)
    row_selector: Optional[str] = Field(None, max_length=300)
    name_selector: Optional[str] = Field(None, max_length=300)
    buy_selector: Optional[str] = Field(None, max_length=300)
    sell_selector: Optional[str] = Field(None, max_length=300)
    column_order: Literal["BUY_SELL", "SELL_BUY"] = "BUY_SELL"

    @field_validator("price_url")
    @classmethod
    def validate_price_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not (v.startswith("http://") or v.startswith("https://") or v.startswith("/")):
            raise ValueError("Link bảng giá riêng phải bắt đầu bằng http://, https:// hoặc /")
        return v

    @field_validator("row_selector", "name_selector", "buy_selector", "sell_selector")
    @classmethod
    def validate_css_selector(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        try:
            import soupsieve
            soupsieve.compile(v)
        except Exception as e:
            raise ValueError(f"CSS selector không hợp lệ ('{v}'): {e}")
        return v


class GoldSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Tên cửa hàng vàng")
    url: str = Field(..., min_length=4, max_length=2000, description="Link trang web cửa hàng")
    interval_minutes: int = Field(10, ge=1, le=1440, description="Chu kỳ quét (1 - 1440 phút)")
    is_enabled: bool = Field(True, description="Bật/tắt tự động quét")
    extract_rules: Optional[ExtractRules] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Tên cửa hàng không được để trống.")
        return cleaned

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        cleaned = v.strip()
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            raise ValueError("Link cửa hàng phải bắt đầu bằng http:// hoặc https://")
        return cleaned


class GoldSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = Field(None, min_length=4, max_length=2000)
    interval_minutes: Optional[int] = Field(None, ge=1, le=1440)
    is_enabled: Optional[bool] = None
    extract_rules: Optional[ExtractRules] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Tên cửa hàng không được để trống.")
        return cleaned

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            raise ValueError("Link cửa hàng phải bắt đầu bằng http:// hoặc https://")
        return cleaned


class GoldSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    interval_minutes: int
    is_enabled: bool
    sort_order: int
    extract_rules: Optional[ExtractRules] = None
    last_scan_at: Optional[datetime] = None
    last_status: str = "NEVER"
    last_message: Optional[str] = None
    last_row_count: int = 0
    last_duration_ms: Optional[int] = None
    last_strategy: Optional[str] = None
    created_at: Optional[datetime] = None

    @field_validator("extract_rules", mode="before")
    @classmethod
    def parse_extract_rules_json(cls, v: Any) -> Optional[ExtractRules]:
        if v is None or v == "":
            return None
        if isinstance(v, ExtractRules):
            return v
        if isinstance(v, dict):
            return ExtractRules(**v)
        if isinstance(v, str):
            try:
                data = json.loads(v)
                if isinstance(data, dict):
                    return ExtractRules(**data)
            except Exception:
                return None
        return None


class GoldSourcePublicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    interval_minutes: int
    sort_order: int = 0
    last_scan_at: Optional[datetime] = None
    last_status: str = "NEVER"


class GoldSourceReorderRequest(BaseModel):
    ids: List[int] = Field(..., min_length=1, description="Danh sách ID cửa hàng theo thứ tự mới")


class GoldSourceBulkIntervalRequest(BaseModel):
    interval_minutes: int = Field(..., ge=1, le=1440, description="Chu kỳ quét áp dụng cho tất cả cửa hàng")


class GoldSourceTestDraftRequest(BaseModel):
    url: str = Field(..., min_length=4, max_length=2000)
    extract_rules: Optional[ExtractRules] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        cleaned = v.strip()
        if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
            raise ValueError("Link cửa hàng phải bắt đầu bằng http:// hoặc https://")
        return cleaned


class GoldSourcePreviewItem(BaseModel):
    gold_type: str
    buy_price: float
    sell_price: float
    price_date: Optional[str] = None


class GoldSourceTestResult(BaseModel):
    success: bool
    status: str  # "SUCCESS" | "ERROR"
    message: str
    strategy: Optional[str] = None
    row_count: int = 0
    duration_ms: int = 0
    price_date: Optional[str] = None
    final_url: Optional[str] = None
    preview: List[GoldSourcePreviewItem] = Field(default_factory=list)


class GoldSourceDeletePreview(BaseModel):
    source_id: int
    name: str
    history_count: int
    deleted: bool = False
    message: str = ""


class GoldCardViewModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    source_id: Optional[int] = None
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
    source_id: Optional[int] = None
    batch_time: Optional[datetime] = None
    formatted_batch_time: str
    is_latest: bool
    cards: List[GoldCardViewModel] = Field(default_factory=list)


class CrawlResult(BaseModel):
    saved: int
    message: str
    source_id: Optional[int] = None


class VersionResponse(BaseModel):
    latest_time: int
    source_id: Optional[int] = None


class DeleteBatchRequest(BaseModel):
    ids: List[int] = Field(default_factory=list, description="Danh sách ID bản ghi cần xóa")


class DeleteBatchResult(BaseModel):
    deleted: int
    message: str


class CrawlerConfigUpdate(BaseModel):
    interval_minutes: int = Field(10, ge=1, le=1440, description="Chu kỳ quét giá vàng mặc định tính theo phút (1 - 1440)")
    is_enabled: bool = Field(True, description="Trạng thái kích hoạt tự động quét")
    notify_user_id: Optional[str] = Field(None, description="ID tài khoản nhận tin nhắn lịch sử call (tương thích đơn lẻ)")
    notify_user_ids: Optional[List[str]] = Field(None, description="Danh sách ID các tài khoản Quản lý nhận tin nhắn lịch sử call")
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
    source_id: Optional[int] = None
    source_name: Optional[str] = None
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
    notify_user_ids: List[str] = Field(default_factory=list)
    notify_mode: str = "ALWAYS"
    delete_changed_messages: bool = False
    sender_username: str = "admin"
    last_cleanup_date: Optional[str] = None
    bot_message_count: int = 0
    bot_unchanged_message_count: int = 0
    bot_changed_message_count: int = 0
    recent_logs: List[CrawlerLogItem] = Field(default_factory=list)
