import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable rate limiting during automated tests so limits don't interfere
_enabled = os.getenv("TESTING", "false").lower() != "true"
limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
