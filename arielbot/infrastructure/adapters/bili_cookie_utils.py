import pickle
from urllib.parse import urlsplit, parse_qs
from typing import Optional


def parse_login_cookie(scan_result: dict) -> Optional[dict]:
    try:
        query_str = urlsplit(scan_result["url"]).query
        params = parse_qs(query_str)
        cookies = {k: v[0] for k, v in params.items()}
        cookies.pop("gourl")
        return cookies
    except Exception:
        return None


def serialize_cookie(cookie: dict) -> bytes:
    return pickle.dumps(cookie)


def deserialize_cookie(data: bytes) -> dict:
    return pickle.loads(data)