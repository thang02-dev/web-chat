import asyncio
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.gold import CrawlResult, GoldBatchViewModel, VersionResponse, DeleteBatchRequest, DeleteBatchResult
from app.services.gold_service import gold_price_service
from app.services.gold_crawler_manager import crawler_manager
from app.websocket.gold_sse import gold_sse_manager

logger = logging.getLogger("webchat.api.gold")

router = APIRouter(prefix="/prices", tags=["Gold Prices"])


@router.get("/batches", response_model=List[GoldBatchViewModel])
async def get_batches(
    type: Optional[str] = Query(None, description="Lọc theo loại vàng (ví dụ 'Vàng 9999' hoặc 'ALL')"),
    db: AsyncSession = Depends(get_db)
):
    """
    Trả về lịch sử giá vàng gom nhóm theo từng đợt cập nhật (chronological batches).
    Đợt đầu tiên có cờ is_latest=True.
    Từng thẻ có giá Mua/Bán, độ chênh lệch tăng giảm ▲/▼ và khoảng chênh lệch Mua - Bán.
    """
    return await gold_price_service.get_price_batches(db, gold_type_filter=type)


@router.get("/types", response_model=List[str])
async def get_gold_types(db: AsyncSession = Depends(get_db)):
    """Trả về danh sách tất cả các loại vàng phục vụ bộ lọc tìm kiếm."""
    return await gold_price_service.get_all_gold_types(db)


@router.get("/version", response_model=VersionResponse)
async def get_version(db: AsyncSession = Depends(get_db)):
    """Trả về epoch millis của đợt cập nhật mới nhất cho client polling dự phòng."""
    latest_time = await gold_price_service.get_latest_update_time_millis(db)
    return VersionResponse(latest_time=latest_time)


@router.get("/config")
async def get_crawler_public_config():
    """Trả về chu kỳ quét công khai cho Navbar hiển thị badge."""
    return {
        "interval_minutes": crawler_manager.interval_minutes,
        "is_enabled": crawler_manager.is_enabled
    }


@router.post("/crawl", response_model=CrawlResult)
async def trigger_crawl(db: AsyncSession = Depends(get_db)):
    """
    Kích hoạt quét giá vàng thủ công tức thì từ hieuvangtru.vn.
    Lưu bản ghi mới khi có biến động giá và tự động phát tín hiệu SSE tới client.
    """
    try:
        res = await crawler_manager.trigger_crawl(source="MANUAL")
        return CrawlResult(saved=res["saved"], message=res["message"])
    except Exception as e:
        logger.error(f"Manual crawl failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"saved": 0, "message": f"Quét thất bại: {str(e)}"}
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
            message=f"Đã xóa thành công {deleted} bản ghi giá vàng."
        )
    except Exception as e:
        logger.error(f"Xóa đợt giá vàng thất bại: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"deleted": 0, "message": f"Xóa thất bại: {str(e)}"}
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
            # Gửi gói handshake ban đầu
            yield f"event: connected\ndata: {json.dumps({'status': 'ready'})}\n\n"

            while True:
                if await request.is_disconnected():
                    break

                try:
                    # Chờ tin nhắn broadcast hoặc gửi heartbeat ping mỗi 25s
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
            "X-Accel-Buffering": "no"
        }
    )

