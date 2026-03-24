from slowapi import Limiter
from slowapi.util import get_remote_address

# Global default rate limiter using the client's IP Address
limiter = Limiter(key_func=get_remote_address)
