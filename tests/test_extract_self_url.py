"""메인 UI 자기 URL 분석 차단."""
import pytest

from deconstructor.web.extract import assert_not_self_ui_url, is_deconstructor_self_url


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://127.0.0.1:8765/", True),
        ("http://127.0.0.1:8765", True),
        ("http://localhost:8765/", True),
        ("http://127.0.0.1:8765/index.html", True),
        ("http://127.0.0.1:8765/graph_output.html", False),
        ("http://127.0.0.1:8765/debug.html", False),
        ("https://example.com/news", False),
    ],
)
def test_is_deconstructor_self_url(url: str, expected: bool) -> None:
    assert is_deconstructor_self_url(url) is expected


def test_assert_not_self_ui_url_raises() -> None:
    with pytest.raises(ValueError, match="메인 UI"):
        assert_not_self_ui_url("http://127.0.0.1:8765/")
