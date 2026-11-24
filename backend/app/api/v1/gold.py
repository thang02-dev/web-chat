import asyncio
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.gold import (
    CrawlResult,
    DeleteBatchRequest,
    DeleteBatchResult,
    GoldBatchViewModel,
    GoldSourcePublicOut,
    VersionResponse,
)
from app.services.gold_crawler_manager import crawler_manager
from app.services.gold_service import GoldSourceService, gold_price_service
from app.websocket.gold_sse import gold_sse_manager

logger = logging.getLogger("webchat.api.gold")

router = APIRouter(prefix="/prices", tags=["Gold Prices"])


@router.get("/sources", response_model=List[GoldSourcePublicOut])
async def get_public_sources(db: AsyncSession = Depends(get_db)):
    """
    Trả về danh sách các cửa hàng giá vàng đang bật theo thứ tự hiển thị (sort_order).
    Cửa hàng đầu tiên trong danh sách là cửa hàng mặc định.
    """
    sources = await GoldSourceService.list_sources(db, enabled_only=True)
    return [GoldSourcePublicOut.model_validate(s) for s in sources]


@router.get("/batches", response_model=List[GoldBatchViewModel])
async def get_batches(
    type: Optional[str] = Query(None, description="Lọc theo loại vàng (ví dụ 'Vàng 9999' hoặc 'ALL')"),
    source_id: Optional[int] = Query(None, description="ID cửa hàng giá vàng (bỏ trống sẽ lấy cửa hàng đầu tiên)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Trả về lịch sử giá vàng gom nhóm theo từng đợt cập nhật (chronological batches) của cửa hàng được chọn.
    """
    return await gold_price_service.get_price_batches(db, gold_type_filter=type, source_id=source_id)


@router.get("/types", response_model=List[str])
async def get_gold_types(
    source_id: Optional[int] = Query(None, description="ID cửa hàng giá vàng"),
    db: AsyncSession = Depends(get_db),
):
    """Trả về danh sách các loại vàng của cửa hàng được chọn phục vụ bộ lọc."""
    return await gold_price_service.get_all_gold_types(db, source_id=source_id)


@router.get("/version", response_model=VersionResponse)
async def get_version(
    source_id: Optional[int] = Query(None, description="ID cửa hàng giá vàng"),
    db: AsyncSession = Depends(get_db),
):
    """Trả về epoch millis của đợt cập nhật mới nhất cho client polling dự phòng."""
    latest_time = await gold_price_service.get_latest_update_time_millis(db, source_id=source_id)
    return VersionResponse(latest_time=latest_time, source_id=source_id)


@router.get("/config")
async def get_crawler_public_config(
    source_id: Optional[int] = Query(None, description="ID cửa hàng đang xem"),
    db: AsyncSession = Depends(get_db),
):
    """Trả về chu kỳ quét công khai của cửa hàng đang xem cho Navbar hiển thị badge."""
    target = (
        await GoldSourceService.get_source(db, source_id)
        if source_id is not None
        else await GoldSourceService.get_default_source(db)
    )
    if target is not None:
        return {
            "source_id": target.id,
            "source_name": target.name,
            "source_url": target.url,
            "interval_minutes": target.interval_minutes if source_id is not None else crawler_manager.interval_minutes,
            "is_enabled": bool(crawler_manager.is_enabled and target.is_enabled),
        }
    return {
        "source_id": None,
        "source_name": None,
        "source_url": None,
        "interval_minutes": crawler_manager.interval_minutes,
        "is_enabled": crawler_manager.is_enabled,
    }


@router.post("/crawl", response_model=CrawlResult)
async def trigger_crawl(
    source_id: Optional[int] = Query(None, description="ID cửa hàng cần quét (bỏ trống sẽ quét cửa hàng đầu tiên)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Kích hoạt quét giá vàng thủ công tức thì cho cửa hàng đang chọn.
    Lưu bản ghi mới khi có biến động giá và phát tín hiệu SSE tới client.
    """
    clean_source_id = source_id if isinstance(source_id, int) else None
    if clean_source_id is not None:
        src = await GoldSourceService.get_source(db, clean_source_id)
        if src is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy cửa hàng giá vàng.",
            )

    try:
        res = await crawler_manager.trigger_crawl(source="MANUAL", db=db, source_id=clean_source_id)
        return CrawlResult(
            saved=res["saved"],
            message=res["message"],
            source_id=res.get("source_id"),
        )
    except Exception as e:
        logger.error(f"Manual crawl failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"saved": 0, "message": f"Quét thất bại: {str(e)}", "source_id": clean_source_id},
        )


@router.post("/batch/delete", response_model=DeleteBatchResult)
@router.delete("/batch", response_model=DeleteBatchResult)
async def delete_batch(payload: DeleteBatchRequest, db: AsyncSession = Depends(get_db)):
    """
    Xóa một đợt giá vàng theo danh sách ID các thẻ.
    Phát tín hiệu SSE để cập nhật tự động toàn bộ client đang mở bảng giá.
    """
    try:
        deleted = await gold_price_service.delete_price_batch(db, payload.ids)
        return DeleteBatchResult(
            deleted=deleted,
            message=f"Đã xóa thành công {deleted} bản ghi giá vàng.",
        )
    except Exception as e:
        logger.error(f"Xóa đợt giá vàng thất bại: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"deleted": 0, "message": f"Xóa thất bại: {str(e)}"},
        )


@router.get("/stream")
async def stream_prices(request: Request):
    """
    Kênh Server-Sent Events (SSE) thời gian thực.
    Các trình duyệt đang mở trang Giá Vàng sẽ nhận event 'price-update' tức thì khi có giá mới.
    """
    queue = gold_sse_manager.subscribe()

    async def event_generator():
        try:
            yield f"event: connected\ndata: {json.dumps({'status': 'ready'})}\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    message = await asyncio.wait_for(queue.get(), timeout=25.0)
                    yield message
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            gold_sse_manager.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
