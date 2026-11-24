import asyncio
from ipaddress import ip_address, ip_network
from typing import Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import httpx

BLOCKED_NETS = [
    ip_network(n)
    for n in (
        "127.0.0.0/8",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
        "0.0.0.0/8",
        "100.64.0.0/10",
        "::1/128",
        "fc00::/7",
        "fe80::/10",
        "::/128",
    )
]

BLOCKED_HOSTNAMES = {"localhost", "0.0.0.0", "::1"}
BLOCKED_HOST_SUFFIXES = (".local", ".internal", ".localhost")

ALLOWED_CONTENT_TYPE_PREFIXES = (
    "text/",
    "application/json",
    "application/xhtml+xml",
    "application/xml",
    "application/javascript",
)

MAX_RESPONSE_BYTES = 3 * 1024 * 1024  # 3 MB
MAX_REDIRECTS = 3


class UnsafeUrlError(ValueError):
    """Ném ra khi URL vi phạm chính sách chống SSRF hoặc vượt giới hạn an toàn."""


def _check_ip_safe(ip_str: str) -> None:
    ip = ip_address(ip_str)
    if (
        any(ip in net for net in BLOCKED_NETS)
        or ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        raise UnsafeUrlError(f"Không cho phép truy cập địa chỉ mạng nội bộ ({ip_str}).")


async def validate_public_url(url: str) -> str:
    """
    Kiểm tra URL hợp lệ (http/https) và không phân giải về địa chỉ IP nội bộ / loopback / link-local.
    """
    if not url or not isinstance(url, str):
        raise UnsafeUrlError("Chỉ chấp nhận link http/https hợp lệ.")

    cleaned = url.strip()
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise UnsafeUrlError("Chỉ chấp nhận link http/https hợp lệ.")

    hostname = parsed.hostname.strip().lower()
    if hostname in BLOCKED_HOSTNAMES or hostname.endswith(BLOCKED_HOST_SUFFIXES):
        raise UnsafeUrlError("Không cho phép truy cập địa chỉ mạng nội bộ.")

    # Kiểm tra nếu hostname là địa chỉ IP trực tiếp
    try:
        _check_ip_safe(hostname)
        return cleaned
    except UnsafeUrlError:
        raise
    except ValueError:
        pass

    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname, port)
    except Exception as e:
        raise ValueError(f"Không thể phân giải tên miền '{hostname}': {e}") from e

    if not infos:
        raise ValueError(f"Không thể phân giải tên miền '{hostname}'.")

    for *_, sockaddr in infos:
        ip_str = sockaddr[0]
        # Bỏ phần scope id nếu là IPv6 (ví dụ fe80::1%eth0)
        if "%" in ip_str:
            ip_str = ip_str.split("%", 1)[0]
        _check_ip_safe(ip_str)

    return cleaned


async def safe_fetch_text(
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 15.0,
    max_redirects: int = MAX_REDIRECTS,
    max_bytes: int = MAX_RESPONSE_BYTES,
    client: Optional[httpx.AsyncClient] = None,
) -> Tuple[str, str]:
    """
    Tải nội dung văn bản từ URL công khai với lớp bảo vệ SSRF:
    - Kiểm tra DNS/IP trước mỗi request và mỗi bước redirect (tối đa 3 lần).
    - Kiểm tra Content-Type hợp lệ.
    - Giới hạn kích thước tải tối đa 3 MB.
    Trả về (text, final_url).
    """
    current_url = url.strip()

    async def _do_fetch(c: httpx.AsyncClient) -> Tuple[str, str]:
        nonlocal current_url
        for hop in range(max_redirects + 1):
            current_url = await validate_public_url(current_url)

            async with c.stream("GET", current_url, follow_redirects=False) as resp:
                if resp.status_code in (301, 302, 303, 307, 308):
                    if hop >= max_redirects:
                        raise UnsafeUrlError(f"Quá số lần chuyển hướng cho phép (tối đa {max_redirects} lần).")
                    location = resp.headers.get("location")
                    if not location:
                        raise ValueError("Máy chủ trả về mã chuyển hướng nhưng thiếu header Location.")
                    current_url = urljoin(current_url, location.strip())
                    continue

                resp.raise_for_status()

                content_type = (resp.headers.get("content-type") or "").strip().lower()
                if content_type and not any(content_type.startswith(p) for p in ALLOWED_CONTENT_TYPE_PREFIXES):
                    raise UnsafeUrlError(f"Định dạng nội dung không được hỗ trợ ({content_type}).")

                content_length = resp.headers.get("content-length")
                if content_length and content_length.isdigit() and int(content_length) > max_bytes:
                    raise UnsafeUrlError("Dung lượng phản hồi vượt quá giới hạn 3 MB.")

                chunks = []
                total = 0
                async for chunk in resp.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        raise UnsafeUrlError("Dung lượng phản hồi vượt quá giới hạn 3 MB.")
                    chunks.append(chunk)

                raw_bytes = b"".join(chunks)
                encoding = resp.encoding or "utf-8"
                try:
                    text = raw_bytes.decode(encoding, errors="replace")
                except LookupError:
                    text = raw_bytes.decode("utf-8", errors="replace")
                return text, current_url

        raise UnsafeUrlError(f"Quá số lần chuyển hướng cho phép (tối đa {max_redirects} lần).")

    if client is not None:
        return await _do_fetch(client)

    async with httpx.AsyncClient(headers=headers, timeout=timeout, follow_redirects=False) as new_client:
        return await _do_fetch(new_client)

