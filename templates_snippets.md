# Code Templates and Snippets

## UI Route with CSRF Protection

```python
@router.get("/page", response_class=HTMLResponse)
async def page_view(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Render a page with CSRF token"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    # Generate CSRF token
    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "page.html",
        {
            "request": request,
            "user": current_user,
            "csrf_token": csrf_token,  # Pass to template
        }
    )

    # Set CSRF cookie
    set_csrf_cookie(response, csrf_token)

    return response


@router.post("/action", response_class=HTMLResponse)
@auth_limiter.limit("5/minute")
async def handle_action(
    request: Request,
    csrf: str = Form(...),  # CSRF token from form
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Handle form submission with CSRF verification"""
    client_ip = get_ip_from_request(request)
    logger.info(f"Action attempt: email={current_user.email}, ip={client_ip}")

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed: email={current_user.email}, ip={client_ip}, error={str(e)}")
        return templates.TemplateResponse(
            "fragments/auth_error.html",
            {
                "request": request,
                "error": "Security validation failed. Please refresh and try again."
            }
        )

    # Your logic here

    # Return success fragment
    return templates.TemplateResponse(
        "fragments/success.html",
        {"request": request}
    )
```

## HTML Form with CSRF

```html
<form hx-post="/action"
      hx-target="#message"
      hx-swap="innerHTML">

    <!-- CSRF Token (REQUIRED) -->
    <input type="hidden" name="csrf" value="{{ csrf_token }}">

    <!-- Form fields -->
    <input type="text" name="field_name" required>

    <button type="submit">Submit</button>
</form>
```

## Database Update Pattern

```python
# Get fresh instance from database (avoid detached instance errors)
db_user = session.get(User, current_user.id)
if not db_user:
    return error_response

# Update fields
db_user.field = new_value

# Save changes
session.add(db_user)
session.commit()
```

## Testing Pattern for UI Routes

```python
def test_ui_route_with_csrf(client: TestClient, session: Session):
    """Test UI route with CSRF protection"""
    # Create and login user
    user = User(email="test@example.com", hashed_password=get_password_hash("password"))
    session.add(user)
    session.commit()

    # Login
    client.post("/auth/token", data={"username": "test@example.com", "password": "password"})

    # Get page to obtain CSRF token
    response = client.get("/page")
    assert response.status_code == 200
    csrf_token = client.cookies.get("csrftoken")

    # Submit form with CSRF
    response = client.post("/action", data={
        "csrf": csrf_token,
        "field": "value"
    })
    assert response.status_code == 200
```

## Common Imports for UI Routes

```python
from fastapi import APIRouter, Request, Response, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from typing import Optional

from app.database import get_session
from app.models import User
from app.login_manager import manager, get_current_user_optional
from app.security import generate_csrf_token, set_csrf_cookie, verify_csrf
from app.rate_limit import auth_limiter
from app.templates_config import templates
from app.logging_config import get_client_ip

import logging
logger = logging.getLogger(__name__)
```