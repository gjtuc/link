"""
Windows·회사 SSL 프록시(PRISM 등) 환경에서 Python HTTPS 신뢰
============================================================

문제
----
Python 기본 CA 번들(certifi)은 Windows 인증서 저장소를 쓰지 않습니다.
ARA SSL PRISM 같은 HTTPS 검사 프록시가 있으면 Tavily·Google 모두
``CERTIFICATE_VERIFY_FAILED`` 가 납니다.

해결
----
``pip-system-certs`` 가 requests/urllib3 가 Windows 루트 CA 저장소를
쓰도록 패치합니다 (Chrome·Edge와 동일한 신뢰 목록).

수동 CA 파일이 필요하면 환경 변수 ``SSL_CERT_FILE`` 또는
``REQUESTS_CA_BUNDLE`` (local_settings 에서 설정 가능).
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)
_bootstrapped = False


def bootstrap_ssl_trust() -> None:
    """한 번만 호출 — Windows면 시스템 CA, 그 외는 certifi 유지."""
    global _bootstrapped
    if _bootstrapped:
        return
    _bootstrapped = True

    if os.getenv("SSL_CERT_FILE") or os.getenv("REQUESTS_CA_BUNDLE"):
        logger.debug("ssl_trust: custom CA bundle env set — skip pip-system-certs")
        return

    if os.name != "nt":
        return

    try:
        import pip_system_certs.wrapt_requests  # noqa: F401
        try:
            import pip_system_certs.wrapt_urllib3  # noqa: F401
        except ImportError:
            pass
    except ImportError:
        logger.warning(
            "pip-system-certs not installed — HTTPS may fail behind corporate SSL proxy. "
            "Run: pip install pip-system-certs"
        )
        return

    logger.debug("ssl_trust: using Windows certificate store via pip-system-certs")
