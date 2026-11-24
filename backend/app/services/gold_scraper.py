import asyncio
import json
import logging
import re
import time
import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, List, Optional, Tuple, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag
import httpx

from app.core.config import settings
from app.schemas.gold import ExtractRules, GoldPriceDto
from app.services.url_guard import safe_fetch_text

logger = logging.getLogger("webchat.gold.scraper")

DATE_PATTERN = re.compile(r"(\d{2}[/-]\d{2}[/-]\d{4})")
AJAX_URL_PATTERN = re.compile(
    r"""['"]((?:https?://|/)[^'"\s<>]*?(?:load_bang_gia|bang[_-]?gia|gia[_-]?vang|banggia|giavang|gold[_-]?price)[^'"\s<>]*?)['"]""",
    re.IGNORECASE,
)

HEADER_BUY_KEYWORDS = ("mua vao", "gia mua", "mua")
HEADER_SELL_KEYWORDS = ("ban ra", "gia ban", "ban")
IGNORED_NAME_KEYWORDS = (
    "loai vang",
    "hieu vang",
    "bang gia",
    "don vi tinh",
    "dvt",
    "cap nhat luc",
    "luu y",
)


@dataclass
class ScrapeResult:
    prices: List[GoldPriceDto]
    strategy: str  # "CSS" | "TABLE" | "DIV_GRID" | "AJAX_DISCOVERY" | "HEURISTIC" | "NONE"
    price_date: Optional[str]
    final_url: str
    duration_ms: int


def sanitize(text: str) -> str:
    """Làm sạch khoảng trắng thừa và non-breaking spaces."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def strip_accents(text: str) -> str:
    """Bỏ dấu tiếng Việt và chuyển về chữ thường để so khớp tiêu đề cột."""
    if not text:
        return ""
    s = sanitize(text).lower().replace("đ", "d")
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def parse_price(text: str) -> Optional[Decimal]:
    """
    Chuyển chuỗi giá dạng '12.980.000', '11,900,000 đ' thành Decimal.
    Trả về None nếu không phải số hợp lệ hoặc < 1000.
    """
    if not text:
        return None
    s = sanitize(text)
    if not s:
        return None
    # Tránh nhận nhầm chuỗi ngày tháng hoặc giờ (ví dụ 24/11/2026, 08:56)
    if DATE_PATTERN.search(s) or re.search(r"\b\d{1,2}:\d{2}\b", s):
        return None

    # Nếu có phần thập phân .00 ở cuối sau số nguyên (ví dụ 12000000.00)
    s_no_dec = re.sub(r"^(\d{4,})\.0{1,2}$", r"\1", s)
    cleaned = re.sub(r"[^\d]", "", s_no_dec)
    if not cleaned:
        return None
    try:
        val = Decimal(cleaned)
        if val < Decimal("1000"):
            return None
        return val
    except Exception:
        return None


def extract_price_date(soup: BeautifulSoup) -> str:
    text = soup.get_text(" ", strip=True)
    m = DATE_PATTERN.search(text)
    if m:
        return m.group(1).replace("-", "/")
    return ""


def _classify_header_cell(text: str) -> Optional[str]:
    norm = strip_accents(text)
    if not norm or len(norm) > 40:
        return None
    for kw in HEADER_BUY_KEYWORDS:
        if kw in norm:
            return "buy"
    for kw in HEADER_SELL_KEYWORDS:
        if kw in norm:
            return "sell"
    if any(k in norm for k in ("loai vang", "san pham", "ten vang", "loai", "hieu vang")):
        return "name"
    return None


def _is_ignored_gold_name(name: str) -> bool:
    if not name:
        return True
    norm = strip_accents(name)
    if not norm or len(norm) > 100:
        return True
    if norm in ("loai vang", "mua vao", "ban ra", "gia mua", "gia ban", "stt"):
        return True
    if any(norm.startswith(k) for k in IGNORED_NAME_KEYWORDS):
        return True
    return False


def _normalize_rows(raw_rows: List[Tuple[str, Optional[Decimal], Optional[Decimal]]], price_date: str) -> List[GoldPriceDto]:
    """
    Chuẩn hóa danh sách (gold_type, buy_price, sell_price):
    - Bỏ dòng rỗng / tiêu đề
    - Giá phải > 0; nếu sell < buy thì tự đảo lại và giữ thứ tự dòng của web
    - Khử trùng lặp theo tên loại vàng (giữ dòng đầu tiên)
    """
    results: List[GoldPriceDto] = []
    seen_names = set()

    for raw_name, buy_val, sell_val in raw_rows:
        name = sanitize(raw_name)
        if _is_ignored_gold_name(name):
            continue
        if buy_val is None or sell_val is None:
            continue
        if buy_val <= 0 or sell_val <= 0:
            continue

        if sell_val < buy_val:
            logger.debug(f"Swapping buy/sell for '{name}' because sell ({sell_val}) < buy ({buy_val})")
            buy_val, sell_val = sell_val, buy_val

        key = strip_accents(name)
        if key in seen_names:
            continue
        seen_names.add(key)

        results.append(
            GoldPriceDto(
                gold_type=name,
                buy_price=buy_val,
                sell_price=sell_val,
                price_date=price_date,
            )
        )

    return results


def _extract_with_css_rules(soup: BeautifulSoup, rules: ExtractRules, price_date: str) -> List[GoldPriceDto]:
    if not rules.row_selector:
        return []
    rows = soup.select(rules.row_selector)
    raw: List[Tuple[str, Optional[Decimal], Optional[Decimal]]] = []

    for row in rows:
        name_text = ""
        buy_val: Optional[Decimal] = None
        sell_val: Optional[Decimal] = None

        if rules.name_selector:
            el = row.select_one(rules.name_selector)
            name_text = el.get_text(" ", strip=True) if el else ""

        if rules.buy_selector and rules.sell_selector:
            b_el = row.select_one(rules.buy_selector)
            s_el = row.select_one(rules.sell_selector)
            buy_val = parse_price(b_el.get_text(" ", strip=True)) if b_el else None
            sell_val = parse_price(s_el.get_text(" ", strip=True)) if s_el else None

        if not name_text or buy_val is None or sell_val is None:
            cells = [c for c in row.find_all(["th", "td", "div", "span"], recursive=False)]
            if len(cells) < 3:
                cells = row.select("th, td")
            if len(cells) >= 3:
                if not name_text:
                    name_text = cells[0].get_text(" ", strip=True)
                p1 = parse_price(cells[1].get_text(" ", strip=True))
                p2 = parse_price(cells[2].get_text(" ", strip=True))
                if buy_val is None or sell_val is None:
                    if rules.column_order == "SELL_BUY":
                        sell_val, buy_val = p1, p2
                    else:
                        buy_val, sell_val = p1, p2

        raw.append((name_text, buy_val, sell_val))

    return _normalize_rows(raw, price_date)


def _extract_tables_with_header(soup: BeautifulSoup, price_date: str) -> List[GoldPriceDto]:
    """Chiến lược TABLE: Tìm bảng <table> có dòng tiêu đề chứa cả cột Mua và cột Bán."""
    tables = soup.select(".modal-body table, #modalGia table, [class*='modal'] table") + soup.select("table")
    seen_tables = set()

    for table in tables:
        if id(table) in seen_tables:
            continue
        seen_tables.add(id(table))

        rows = table.select("tr")
        if len(rows) < 2:
            continue

        buy_idx: Optional[int] = None
        sell_idx: Optional[int] = None
        name_idx: int = 0
        header_row_idx: int = -1

        for r_idx, row in enumerate(rows[:4]):
            cells = row.select("th, td")
            if len(cells) < 3:
                continue
            b_i, s_i, n_i = None, None, None
            for c_idx, cell in enumerate(cells):
                role = _classify_header_cell(cell.get_text(" ", strip=True))
                if role == "buy" and b_i is None:
                    b_i = c_idx
                elif role == "sell" and s_i is None:
                    s_i = c_idx
                elif role == "name" and n_i is None:
                    n_i = c_idx
            if b_i is not None and s_i is not None:
                buy_idx = b_i
                sell_idx = s_i
                if n_i is not None:
                    name_idx = n_i
                else:
                    remaining = [i for i in range(len(cells)) if i not in (b_i, s_i)]
                    name_idx = remaining[0] if remaining else 0
                header_row_idx = r_idx
                break

        if buy_idx is None or sell_idx is None:
            continue

        raw: List[Tuple[str, Optional[Decimal], Optional[Decimal]]] = []
        max_idx = max(name_idx, buy_idx, sell_idx)
        for row in rows[header_row_idx + 1 :]:
            cells = row.select("th, td")
            if len(cells) <= max_idx:
                continue
            name_text = cells[name_idx].get_text(" ", strip=True)
            buy_val = parse_price(cells[buy_idx].get_text(" ", strip=True))
            sell_val = parse_price(cells[sell_idx].get_text(" ", strip=True))
            raw.append((name_text, buy_val, sell_val))

        normalized = _normalize_rows(raw, price_date)
        if normalized:
            return normalized

    return []


def _extract_div_grid(soup: BeautifulSoup, price_date: str) -> List[GoldPriceDto]:
    """
    Chiến lược DIV_GRID: Nhận diện bảng giá dựng bằng lưới <div> (như ngocthinh-jewelry.vn).
    Tìm hàng tiêu đề có >= 3 phần tử con chứa cả 'Mua vào' và 'Bán ra', sau đó đọc các hàng dữ liệu kế tiếp.
    """
    raw: List[Tuple[str, Optional[Decimal], Optional[Decimal]]] = []

    for candidate in soup.find_all(["div", "ul", "header", "section"]):
        children = [c for c in candidate.find_all(recursive=False) if isinstance(c, Tag)]
        if len(children) < 3 or len(children) > 8:
            continue

        b_i, s_i, n_i = None, None, None
        for idx, ch in enumerate(children):
            # Chỉ xét các ô tiêu đề ngắn, không phải container lớn
            txt = ch.get_text(" ", strip=True)
            if len(txt) > 35:
                b_i = s_i = None
                break
            role = _classify_header_cell(txt)
            if role == "buy" and b_i is None:
                b_i = idx
            elif role == "sell" and s_i is None:
                s_i = idx
            elif role == "name" and n_i is None:
                n_i = idx

        if b_i is None or s_i is None:
            continue

        if n_i is None:
            remaining = [i for i in range(len(children)) if i not in (b_i, s_i)]
            n_i = remaining[0] if remaining else 0

        max_idx = max(n_i, b_i, s_i)

        # Tìm các hàng dữ liệu trong các sibling kế tiếp hoặc cùng parent
        row_candidates: List[Tag] = []
        for sib in candidate.find_next_siblings():
            if not isinstance(sib, Tag):
                continue
            sib_children = [c for c in sib.find_all(recursive=False) if isinstance(c, Tag)]
            # Trường hợp 1: sibling là container chứa các dòng (như .contenttogoldflex > div)
            if sib_children and all(
                len([gc for gc in sc.find_all(recursive=False) if isinstance(gc, Tag)]) > max_idx
                for sc in sib_children[:3]
            ):
                row_candidates.extend(sib_children)
            # Trường hợp 2: mỗi sibling trực tiếp là một dòng dữ liệu
            elif len(sib_children) > max_idx:
                row_candidates.append(sib)

        for r_tag in row_candidates:
            cells = [c for c in r_tag.find_all(recursive=False) if isinstance(c, Tag)]
            if len(cells) <= max_idx:
                continue
            name_text = cells[n_i].get_text(" ", strip=True)
            buy_val = parse_price(cells[b_i].get_text(" ", strip=True))
            sell_val = parse_price(cells[s_i].get_text(" ", strip=True))
            raw.append((name_text, buy_val, sell_val))

        normalized = _normalize_rows(raw, price_date)
        if normalized:
            return normalized

    return []


def _extract_tables_heuristic(soup: BeautifulSoup, price_date: str) -> List[GoldPriceDto]:
    """Chiến lược dự phòng HEURISTIC: Bảng >= 3 cột không có tiêu đề rõ ràng, lấy max=Bán, min=Mua."""
    tables = soup.select(".modal-body table, #modalGia table, [class*='modal'] table") + soup.select("table")
    seen_tables = set()
    raw: List[Tuple[str, Optional[Decimal], Optional[Decimal]]] = []

    for table in tables:
        if id(table) in seen_tables:
            continue
        seen_tables.add(id(table))

        for row in table.select("tr"):
            cells = row.select("th, td")
            if len(cells) < 3:
                continue
            name_text = cells[0].get_text(" ", strip=True)
            col2 = parse_price(cells[1].get_text(" ", strip=True))
            col3 = parse_price(cells[2].get_text(" ", strip=True))
            if col2 is None or col3 is None:
                continue
            sell_price = max(col2, col3)
            buy_price = min(col2, col3)
            raw.append((name_text, buy_price, sell_price))

    return _normalize_rows(raw, price_date)


def parse_html_with_strategy(
    html: str,
    rules: Optional[ExtractRules] = None,
) -> Tuple[List[GoldPriceDto], str, str]:
    """
    Phân tích chuỗi HTML và trả về (danh sách GoldPriceDto, tên chiến lược, ngày giá).
    """
    if not html or not html.strip():
        return [], "NONE", ""

    soup = BeautifulSoup(html, "html.parser")
    price_date = extract_price_date(soup)

    if rules and rules.mode == "CSS" and rules.row_selector:
        prices = _extract_with_css_rules(soup, rules, price_date)
        return prices, "CSS", price_date

    # 1. TABLE có tiêu đề cột Mua vào / Bán ra
    prices = _extract_tables_with_header(soup, price_date)
    if prices:
        return prices, "TABLE", price_date

    # 2. DIV_GRID có tiêu đề cột Mua vào / Bán ra
    prices = _extract_div_grid(soup, price_date)
    if prices:
        return prices, "DIV_GRID", price_date

    # 3. HEURISTIC trên các bảng 3 cột
    prices = _extract_tables_heuristic(soup, price_date)
    if prices:
        return prices, "HEURISTIC", price_date

    return [], "NONE", price_date


def discover_ajax_price_urls(html: str, base_url: str) -> List[str]:
    """Dò tìm đường dẫn AJAX tải bảng giá bên trong mã nguồn HTML/Script."""
    candidates: List[str] = []
    for m in AJAX_URL_PATTERN.finditer(html or ""):
        raw_path = m.group(1).strip()
        full = urljoin(base_url, raw_path)
        if full not in candidates:
            candidates.append(full)

    # Fallback quen thuộc cho hieuvangtru.vn nếu có modal bảng giá
    if "load_bang_gia.php" not in base_url and ("modal-bang-gia" in html or "bang-gia-online-btn" in html):
        fallback = base_url.rstrip("/") + "/layout/load_bang_gia.php"
        if fallback not in candidates:
            candidates.append(fallback)

    return candidates[:3]


def coerce_extract_rules(rules: Optional[Union[ExtractRules, str, dict]]) -> Optional[ExtractRules]:
    if rules is None or rules == "":
        return None
    if isinstance(rules, ExtractRules):
        return rules
    if isinstance(rules, dict):
        return ExtractRules(**rules)
    if isinstance(rules, str):
        try:
            data = json.loads(rules)
            if isinstance(data, dict):
                return ExtractRules(**data)
        except Exception:
            return None
    return None


async def scrape(
    url: str,
    rules: Optional[Union[ExtractRules, str, dict]] = None,
    *,
    retries: int = 3,
    timeout: Optional[float] = None,
    headers: Optional[dict] = None,
    client: Optional[httpx.AsyncClient] = None,
) -> ScrapeResult:
    """
    Quét bảng giá vàng từ một URL bất kỳ với cơ chế chống SSRF, tự nhận dạng đa chiến lược
    (TABLE -> DIV_GRID -> AJAX_DISCOVERY -> HEURISTIC) hoặc theo luật CSS tùy chỉnh.
    """
    start_ts = time.perf_counter()
    parsed_rules = coerce_extract_rules(rules)
    req_timeout = timeout if timeout is not None else settings.CRAWLER_TIMEOUT_SECONDS
    req_headers = headers if headers is not None else {"User-Agent": settings.CRAWLER_USER_AGENT}

    target_url = url.strip()
    if parsed_rules and parsed_rules.price_url:
        target_url = urljoin(target_url, parsed_rules.price_url.strip())

    last_error: Optional[Exception] = None
    max_attempts = max(1, retries)

    for attempt in range(1, max_attempts + 1):
        try:
            html, final_url = await safe_fetch_text(
                target_url,
                headers=req_headers,
                timeout=req_timeout,
                client=client,
            )
            prices, strategy, price_date = parse_html_with_strategy(html, parsed_rules)

            # Nếu trang chính chưa có bảng giá và đang ở chế độ AUTO -> thử dò endpoint AJAX
            if not prices and (not parsed_rules or parsed_rules.mode == "AUTO"):
                ajax_urls = discover_ajax_price_urls(html, final_url)
                for ajax_url in ajax_urls:
                    try:
                        ajax_html, ajax_final = await safe_fetch_text(
                            ajax_url,
                            headers=req_headers,
                            timeout=req_timeout,
                            client=client,
                        )
                        ajax_prices, _, ajax_date = parse_html_with_strategy(ajax_html, parsed_rules)
                        if ajax_prices:
                            prices = ajax_prices
                            strategy = "AJAX_DISCOVERY"
                            price_date = ajax_date or price_date
                            final_url = ajax_final
                            break
                    except Exception as ajax_err:
                        logger.debug(f"AJAX discovery fetch failed for {ajax_url}: {ajax_err}")

            duration_ms = int((time.perf_counter() - start_ts) * 1000)
            return ScrapeResult(
                prices=prices,
                strategy=strategy,
                price_date=price_date,
                final_url=final_url,
                duration_ms=duration_ms,
            )

        except Exception as e:
            last_error = e
            logger.warning(f"Scrape attempt {attempt}/{max_attempts} for {target_url} failed: {e}")
            # Không retry nếu là lỗi SSRF / URL không hợp lệ
            from app.services.url_guard import UnsafeUrlError
            if isinstance(e, UnsafeUrlError):
                raise
            if attempt < max_attempts:
                await asyncio.sleep(2 ** attempt)

    if last_error:
        raise last_error

    duration_ms = int((time.perf_counter() - start_ts) * 1000)
    return ScrapeResult(prices=[], strategy="NONE", price_date="", final_url=target_url, duration_ms=duration_ms)

