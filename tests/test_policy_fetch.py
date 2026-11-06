import socket
import pytest
import requests
from core import policy_fetch
from core.policy_fetch import UnsafeAddress, check_url, fetch_policy_text, html_to_text

PUBLIC = "93.184.216.34"


@pytest.fixture(autouse=True)
def dns(monkeypatch):
    """Pretend DNS: names containing 'internal' resolve to a private address, everything else to a public one."""
    def fake_getaddrinfo(host, port, *args, **kwargs):
        try:
            import ipaddress
            ipaddress.ip_address(host)
            ip = host
        except ValueError:
            ip = "10.0.0.5" if "internal" in host or host == "localhost" else PUBLIC
            if host == "localhost":
                ip = "127.0.0.1"
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port))]
    monkeypatch.setattr(policy_fetch.socket, "getaddrinfo", fake_getaddrinfo)


@pytest.mark.parametrize("url", [
    "file:///etc/passwd", "ftp://example.com/p", "javascript:alert(1)", "example.com/privacy", "",
    "https://user:pass@example.com/p", "https://example.com:8080/p", "http://localhost/admin",
    "http://127.0.0.1:8501/", "http://10.0.0.7/x", "http://192.168.1.1/", "http://169.254.169.254/latest/meta-data",
    "http://[::1]/", "https://intranet.internal/policy",
])
def test_unsafe_addresses_are_refused(url):
    with pytest.raises(UnsafeAddress):
        check_url(url)


@pytest.mark.parametrize("url", ["https://example.com/privacy", "http://example.com/privacy", "https://" + PUBLIC + "/p"])
def test_normal_public_addresses_are_allowed(url):
    assert check_url(url) == url


class Resp:
    def __init__(self, status=200, body=b"", headers=None, encoding="utf-8"):
        self.status_code, self.headers, self.encoding, self._body = status, headers or {}, encoding, body
        self.closed = False

    def iter_content(self, size):
        for i in range(0, len(self._body), size):
            yield self._body[i:i + size]

    def close(self):
        self.closed = True


HTML = {"Content-Type": "text/html; charset=utf-8"}


def getter_for(*responses):
    queue = list(responses)
    calls = []
    def getter(url, timeout):
        calls.append(url)
        item = queue.pop(0)
        if isinstance(item, Exception):
            raise item
        return item
    getter.calls = calls
    return getter


def test_a_normal_page_is_read():
    page = b"<html><body><h1>Privacy</h1><p>We collect your name.</p><script>evil()</script></body></html>"
    result = fetch_policy_text("https://example.com/p", getter=getter_for(Resp(200, page, HTML)))
    assert result["ok"] and "We collect your name." in result["text"] and "evil" not in result["text"]


def test_a_redirect_to_a_public_page_is_followed():
    getter = getter_for(Resp(301, b"", {"Location": "/real"}), Resp(200, b"<p>Hello policy text</p>", HTML))
    result = fetch_policy_text("https://example.com/p", getter=getter)
    assert result["ok"] and getter.calls[1] == "https://example.com/real"


def test_a_redirect_to_a_private_address_is_blocked():
    getter = getter_for(Resp(302, b"", {"Location": "http://169.254.169.254/latest/meta-data"}))
    result = fetch_policy_text("https://example.com/p", getter=getter)
    assert not result["ok"] and "private or internal" in result["error"] and len(getter.calls) == 1


def test_too_many_redirects_stop():
    hops = [Resp(302, b"", {"Location": "/again"}) for _ in range(10)]
    result = fetch_policy_text("https://example.com/p", getter=getter_for(*hops))
    assert not result["ok"] and "redirected too many times" in result["error"]


def test_big_pages_are_cut_and_marked_truncated():
    result = fetch_policy_text("https://example.com/p", max_bytes=1000,
                               getter=getter_for(Resp(200, b"<p>" + b"a" * 50_000 + b"</p>", HTML)))
    assert result["ok"] and result["truncated"] is True and len(result["text"]) <= 1000


def test_non_text_files_are_refused():
    result = fetch_policy_text("https://example.com/p.pdf", getter=getter_for(Resp(200, b"%PDF", {"Content-Type": "application/pdf"})))
    assert not result["ok"] and "not a web page" in result["error"]


def test_error_pages_give_a_friendly_message():
    result = fetch_policy_text("https://example.com/p", getter=getter_for(Resp(404, b"", HTML)))
    assert not result["ok"] and "404" in result["error"]


def test_network_problems_never_raise():
    for problem, words in [(requests.exceptions.Timeout(), "too long"), (requests.exceptions.ConnectionError(), "Could not reach"),
                           (ValueError("boom"), "Could not read")]:
        result = fetch_policy_text("https://example.com/p", getter=getter_for(problem))
        assert not result["ok"] and words in result["error"]


def test_unsafe_start_address_is_refused_without_any_request():
    getter = getter_for()
    result = fetch_policy_text("http://127.0.0.1:8501/", getter=getter)
    assert not result["ok"] and getter.calls == []


def test_html_to_text_keeps_paragraphs_on_separate_lines_and_drops_scripts_and_menus():
    html = "<nav>Menu</nav><h1>Policy</h1><p>First sentence. Second one.</p><ul><li>Item A</li><li>Item B</li></ul><style>x{}</style>"
    assert html_to_text(html).split("\n") == ["Policy", "First sentence. Second one.", "Item A", "Item B"]
