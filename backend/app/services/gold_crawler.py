import asyncio
import logging
import re
from decimal import Decimal
from typing import List, Optional
from bs4 import BeautifulSoup
import httpx

from app.core.config import settings
from app.schemas.gold import GoldPriceDto

logger = logging.getLogger("webchat.gold.crawler")

DATE_PATTERN = re.compile(r"(\d{2}/\d{2}/\d{4})")


def parse_price(text: str) -> Optional[Decimal]:
    """Parse string like '12.980.000' or '12,980,000 đ' into Decimal."""
    if not text:
        return None
    cleaned = re.sub(r"[^\d]", "", text)
    if not cleaned:
        return None
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def sanitize(text: str) -> str:
    """Clean extra spaces and non-breaking spaces."""
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


class GoldCrawler:
    def __init__(self):
        self.target_url = settings.CRAWLER_TARGET_URL
        self.timeout = settings.CRAWLER_TIMEOUT_SECONDS
        self.headers = {"User-Agent": settings.CRAWLER_USER_AGENT}

    async def fetch_gold_prices(self, max_retries: int = 3) -> List[GoldPriceDto]:
        """
        Crawl hieuvangtru.vn and parse gold prices.
        Retries up to max_retries with exponential backoff on error.
        """
        for attempt in range(1, max_retries + 1):
            try:
                logger.debug(f"Crawling {self.target_url} (attempt {attempt}/{max_retries})")
                async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
                    resp = await client.get(self.target_url)
                    resp.raise_for_status()
                    html = resp.text

                prices = self._parse_document(html)
                # Fallback to dynamic endpoint if homepage yielded 0 rows
                if not prices and "load_bang_gia.php" not in self.target_url:
                    ajax_url = self.target_url.rstrip("/") + "/layout/load_bang_gia.php"
                    logger.debug(f"Initial target yielded 0 rows; attempting {ajax_url}")
                    async with httpx.AsyncClient(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
                        ajax_resp = await client.get(ajax_url)
                        ajax_resp.raise_for_status()
                        prices = self._parse_document(ajax_resp.text)

                logger.debug(f"Crawl successful: {len(prices)} rows parsed.")
                return prices

            except Exception as e:
                logger.warning(f"Crawl attempt {attempt}/{max_retries} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error("All crawl attempts failed. Returning empty list.")
                    return []

        return []

    def _parse_document(self, html: str) -> List[GoldPriceDto]:
        soup = BeautifulSoup(html, "html.parser")
        price_date = self._extract_price_date(soup)

        prices: List[GoldPriceDto] = []

        # Attempt 1: Modal tables
        modal_tables = soup.select(".modal-body table, #modalGia table, [class*='modal'] table")
        if modal_tables:
            prices = self._extract_from_tables(modal_tables, price_date)

        # Attempt 2: Fallback all tables
        if not prices:
            all_tables = soup.select("table")
            prices = self._extract_from_tables(all_tables, price_date)

        return prices

    def _extract_from_tables(self, tables, price_date: Optional[str]) -> List[GoldPriceDto]:
        results: List[GoldPriceDto] = []
        for table in tables:
            rows = table.select("tr")
            for row in rows:
                cells = row.select("th, td")
                if len(cells) < 3:
                    continue

                gold_type = sanitize(cells[0].get_text())
                if (not gold_type or 
                    gold_type.lower() == "loại vàng" or 
                    "hiệu vàng" in gold_type.lower()):
                    continue

                col2 = parse_price(cells[1].get_text())
                col3 = parse_price(cells[2].get_text())

                if col2 is None or col3 is None:
                    continue

                # Heuristic: sell price is higher than buy price
                sell_price = max(col2, col3)
                buy_price = min(col2, col3)

                results.append(GoldPriceDto(
                    gold_type=gold_type,
                    sell_price=sell_price,
                    buy_price=buy_price,
                    price_date=price_date
                ))
        return results

    def _extract_price_date(self, soup: BeautifulSoup) -> Optional[str]:
        text = soup.get_text()
        m = DATE_PATTERN.search(text)
        if m:
            return m.group(1)
        return ""


gold_crawler = GoldCrawler()

