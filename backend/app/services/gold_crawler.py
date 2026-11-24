import logging
from typing import List, Optional, Union
from bs4 import BeautifulSoup

from app.core.config import settings
from app.schemas.gold import ExtractRules, GoldPriceDto
from app.services.gold_scraper import (
    DATE_PATTERN,
    parse_html_with_strategy,
    parse_price,
    sanitize,
    scrape,
)

logger = logging.getLogger("webchat.gold.crawler")


class GoldCrawler:
    def __init__(self):
        self.target_url = settings.CRAWLER_TARGET_URL
        self.timeout = settings.CRAWLER_TIMEOUT_SECONDS
        self.headers = {"User-Agent": settings.CRAWLER_USER_AGENT}

    async def fetch_gold_prices(
        self,
        max_retries: int = 3,
        url: Optional[str] = None,
        rules: Optional[Union[ExtractRules, str, dict]] = None,
    ) -> List[GoldPriceDto]:
        """
        Lớp bọc tương thích ngược gọi sang gold_scraper.scrape().
        """
        target = (url or self.target_url).strip()
        try:
            result = await scrape(
                target,
                rules=rules,
                retries=max_retries,
                timeout=self.timeout,
                headers=self.headers,
            )
            return result.prices
        except Exception as e:
            logger.error(f"All crawl attempts failed for {target}: {e}")
            return []

    def _parse_document(
        self,
        html: str,
        rules: Optional[Union[ExtractRules, str, dict]] = None,
    ) -> List[GoldPriceDto]:
        from app.services.gold_scraper import coerce_extract_rules
        prices, _, _ = parse_html_with_strategy(html, coerce_extract_rules(rules))
        return prices

    def _extract_price_date(self, soup: BeautifulSoup) -> Optional[str]:
        text = soup.get_text()
        m = DATE_PATTERN.search(text)
        if m:
            return m.group(1)
        return ""


gold_crawler = GoldCrawler()
