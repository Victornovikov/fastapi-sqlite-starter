"""
Rate limiting for authentication endpoints to prevent brute force attacks.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

# Create limiter instance using client IP address as key
limiter = Limiter(key_func=get_remote_address)


def get_client_ip(request: Request) -> str:
    """
    Get client IP address from request.
    Checks X-Forwarded-For header for proxy situations.
    """
    # Check for proxy headers
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        # Get the first IP in the chain
        return x_forwarded_for.split(",")[0].strip()

    # Check for X-Real-IP header
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        return x_real_ip

    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"


# Create a limiter for auth endpoints specifically
auth_limiter = Limiter(key_func=get_client_ip)