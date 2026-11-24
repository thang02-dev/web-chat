from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.users import require_admin
from app.core.database import get_db
from app.models.models import User
from app.schemas.gold import (
    GoldSourceBulkIntervalRequest,
    GoldSourceCreate,
    GoldSourceDeletePreview,
    GoldSourceOut,
    GoldSourceReorderRequest,
    GoldSourceTestDraftRequest,
    GoldSourceTestResult,
    GoldSourceUpdate,
)
from app.services.gold_crawler_manager import crawler_manager
from app.services.gold_service import GoldSourceService
from app.services.url_guard import UnsafeUrlError

router = APIRouter(prefix="/admin/gold-sources", tags=["Admin Gold Sources"])


@router.get("", response_model=List[GoldSourceOut])
async def list_gold_sources(
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """(Admin) Lấy danh sách toàn bộ cửa hàng giá vàng theo thứ tự sort_order."""
    sources = await GoldSourceService.list_sources(db, enabled_only=False)
    return [GoldSourceOut.model_validate(s) for s in sources]


@router.post("", response_model=GoldSourceOut, status_code=status.HTTP_201_CREATED)
async def create_gold_source(
    payload: GoldSourceCreate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """(Admin) Thêm cửa hàng giá vàng mới."""
    try:
        src = await GoldSourceService.create_source(db, payload)
        crawler_manager._sleep_event.set()
        return GoldSourceOut.model_validate(src)
    except (UnsafeUrlError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/reorder", response_model=List[GoldSourceOut])
async def reorder_gold_sources(
    payload: GoldSourceReorderRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """(Admin) Cập nhật thứ tự hiển thị cửa hàng sau khi kéo thả."""
    try:
        sources = await GoldSourceService.reorder_sources(db, payload.ids)
        return [GoldSourceOut.model_validate(s) for s in sources]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/interval", response_model=List[GoldSourceOut])
async def set_interval_for_all_sources(
    payload: GoldSourceBulkIntervalRequest,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """(Admin) Áp dụng nhanh một chu kỳ quét cho tất cả cửa hàng và đồng bộ chu kỳ mặc định."""
    sources = await GoldSourceService.set_interval_for_all(db, payload.interval_minutes)
    crawler_manager.interval_minutes = payload.interval_minutes
    await crawler_manager._upsert_setting(db, "crawler_interval_minutes", str(payload.interval_minutes))
    await db.commit()
    crawler_manager._sleep_event.set()
    return [GoldSourceOut.model_validate(s) for s in sources]


@router.post("/test", response_model=GoldSourceTestResult)
async def test_draft_gold_source(
    payload: GoldSourceTestDraftRequest,
    current_admin: User = Depends(require_admin),
):
    """
    (Admin) Quét thử một đường dẫn web và luật bóc tách trước khi lưu.
    Chỉ trả về kết quả xem trước, không lưu dữ liệu giá vào cơ sở dữ liệu.
    """
    return await GoldSourceService.run_test_scrape(payload.url, payload.extract_rules)


@router.post("/{source_id}/test", response_model=GoldSourceTestResult)
async def test_saved_gold_source(
    source_id: int,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    (Admin) Quét thử cửa hàng đã lưu theo ID.
    Cập nhật cột trạng thái quét (Thành công / Thất bại) trên bảng cửa hàng nhưng KHÔNG lưu giá vào lịch sử.
    """
    res = await GoldSourceService.test_saved_source(db, source_id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy cửa hàng giá vàng.")
    return res


@router.patch("/{source_id}", response_model=GoldSourceOut)
async def update_gold_source(
    source_id: int,
    payload: GoldSourceUpdate,
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """(Admin) Cập nhật thông tin cửa hàng giá vàng."""
    try:
        src = await GoldSourceService.update_source(db, source_id, payload)
    except (UnsafeUrlError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if src is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy cửa hàng giá vàng.")
    crawler_manager._sleep_event.set()
    return GoldSourceOut.model_validate(src)


@router.delete("/{source_id}", response_model=GoldSourceDeletePreview)
async def delete_gold_source(
    source_id: int,
    preview: bool = Query(False, description="Nếu preview=true, chỉ trả về số lượng bản ghi lịch sử sẽ bị xóa"),
    current_admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """(Admin) Xóa cửa hàng giá vàng và toàn bộ lịch sử giá của cửa hàng đó."""
    res = await GoldSourceService.delete_source(db, source_id, preview_only=preview)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy cửa hàng giá vàng.")
    return res

