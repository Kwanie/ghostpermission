"""Fetches a privacy policy page safely and turns it into plain text.

The address comes from an app listing or from a user, so it is NOT trusted. Before every request
(and every redirect) we check that it is a normal public web address, never something inside the
user's own computer or network. Pages are size-limited and time-limited."""
import ipaddress
import socket
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

MAX_BYTES = 2_000_000
MAX_REDIRECTS = 3
TIMEOUT = (5, 10)           # seconds to connect, seconds to read
ALLOWED_PORTS = (None, 80, 443)
TEXT_TYPES = ("text/html", "text/plain", "application/xhtml+xml")
USER_AGENT = "Mozilla/5.0 (compatible; GhostPermission policy reader)"


class UnsafeAddress(Exception):
    pass


def check_url(url):
    """Raise UnsafeAddress unless this is a plain public http(s) address."""
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in ("http", "https"):
        raise UnsafeAddress("Only web addresses starting with http:// or https:// are allowed.")
    if not parsed.hostname:
        raise UnsafeAddress("That does not look like a web address.")
    if parsed.username or parsed.password:
        raise UnsafeAddress("Addresses that contain a user name or password are not allowed.")
    try:
        port = parsed.port
    except ValueError:
        raise UnsafeAddress("That address has an invalid port.")
    if port not in ALLOWED_PORTS:
        raise UnsafeAddress("Only the normal web ports are allowed.")
    try:
        infos = socket.getaddrinfo(parsed.hostname, port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror:
        raise UnsafeAddress("That website name could not be found.")
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global or address.is_multicast:
            raise UnsafeAddress("That address points to a private or internal network, so it is not allowed.")
    return parsed.geturl()


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "head", "svg", "nav", "footer", "form", "iframe"}
    BLOCK = {"p", "div", "li", "br", "tr", "section", "article", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip_depth += 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
        elif tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(html):
    """Readable text from a web page. Block elements become line breaks so sentences stay separate."""
    parser = _TextExtractor()
    parser.feed(html or "")
    parser.close()
    lines = ["".join(line.split(" ")) and " ".join(line.split()) for line in "".join(parser.parts).split("\n")]
    return "\n".join(line for line in lines if line)


def _get(url, timeout):
    return requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, stream=True, allow_redirects=False)


def fetch_policy_text(url, max_bytes=MAX_BYTES, getter=None):
    """
    Returns {"ok", "text", "final_url", "truncated", "error"}. Never raises.
    `getter` is only for tests.
    """
    getter = getter or _get
    result = {"ok": False, "text": "", "final_url": url, "truncated": False, "error": ""}
    current = str(url or "").strip()
    try:
        for _ in range(MAX_REDIRECTS + 1):
            current = check_url(current)
            response = getter(current, TIMEOUT)
            if 300 <= response.status_code < 400 and response.headers.get("Location"):
                current = urljoin(current, response.headers["Location"])
                response.close()
                continue
            break
        else:
            result["error"] = "The page redirected too many times."
            return result

        result["final_url"] = current
        if response.status_code != 200:
            result["error"] = f"The website answered with an error (code {response.status_code})."
            response.close()
            return result
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if content_type not in TEXT_TYPES:
            result["error"] = "That address is not a web page or text file."
            response.close()
            return result

        chunks, size = [], 0
        for chunk in response.iter_content(8192):
            size += len(chunk)
            chunks.append(chunk)
            if size > max_bytes:
                result["truncated"] = True
                break
        response.close()
        raw = b"".join(chunks)[:max_bytes]
        text = raw.decode(response.encoding or "utf-8", errors="replace")
        result["text"] = html_to_text(text) if content_type != "text/plain" else text.strip()
        result["ok"] = True
        return result
    except UnsafeAddress as problem:
        result["error"] = str(problem)
    except requests.exceptions.Timeout:
        result["error"] = "The website took too long to answer."
    except requests.exceptions.RequestException:
        result["error"] = "Could not reach that website."
    except Exception as error:
        result["error"] = f"Could not read that page ({type(error).__name__})."
    return result
