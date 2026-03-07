"""Rate limiting (FR-21), secure headers (FR-19)."""
from slowapi import Limiter
from slowapi.util import get_remote_address


def get_remote_address_from_request(request):
    if request.client:
        return request.client.host
    return "127.0.0.1"


limiter = Limiter(key_func=get_remote_address_from_request)
