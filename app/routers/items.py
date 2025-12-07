"""
Items router - Example CRUD operations for user data.

This router demonstrates:
- HTML page rendering with Jinja2
- HTMX-powered form submissions
- JSON API endpoints
- User-scoped data access
- CSRF protection for forms
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session, select, func
from datetime import datetime, timezone
import logging

from app.database import get_session
from app.models import User, Item
from app.schemas import ItemCreate, ItemUpdate, ItemResponse, ItemListResponse
from app.login_manager import manager, get_current_user_optional
from app.logging_config import get_client_ip
from app.security import verify_csrf, generate_csrf_token, set_csrf_cookie
from app.templates_config import templates

logger = logging.getLogger(__name__)
router = APIRouter(tags=["items"])


# ============== HTML Pages ==============

@router.get("/items", response_class=HTMLResponse)
async def items_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
    session: Session = Depends(get_session)
):
    """Render the items list page"""
    if not current_user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    # Get user's items
    items = session.exec(
        select(Item)
        .where(Item.user_id == current_user.id)
        .order_by(Item.created_at.desc())
    ).all()

    # Generate CSRF token
    csrf_token = generate_csrf_token()

    response = templates.TemplateResponse(
        "items.html",
        {
            "request": request,
            "user": current_user,
            "items": items,
            "csrf_token": csrf_token,
        }
    )

    set_csrf_cookie(response, csrf_token)
    return response


# ============== HTMX Endpoints ==============

@router.post("/items/add", response_class=HTMLResponse)
async def add_item(
    request: Request,
    title: str = Form(...),
    content: Optional[str] = Form(None),
    csrf: str = Form(...),
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Add a new item via HTMX form"""
    client_ip = get_client_ip(request)

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed on item add: user={current_user.email}, ip={client_ip}")
        return templates.TemplateResponse(
            "fragments/item_error.html",
            {"request": request, "error": "Security validation failed. Please refresh."}
        )

    # Create new item
    item = Item(
        user_id=current_user.id,
        title=title.strip(),
        content=content.strip() if content else None,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    logger.info(f"Item created: id={item.id}, user={current_user.email}, ip={client_ip}")

    # Return the new item card to prepend to the list
    return templates.TemplateResponse(
        "fragments/item_card.html",
        {"request": request, "item": item, "is_new": True}
    )


@router.delete("/items/{item_id}", response_class=HTMLResponse)
async def delete_item(
    request: Request,
    item_id: int,
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Delete an item via HTMX"""
    client_ip = get_client_ip(request)

    # Get the item
    item = session.get(Item, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.user_id != current_user.id:
        logger.warning(f"Unauthorized delete attempt: user={current_user.email}, item_id={item_id}, ip={client_ip}")
        raise HTTPException(status_code=403, detail="Not authorized to delete this item")

    session.delete(item)
    session.commit()

    logger.info(f"Item deleted: id={item_id}, user={current_user.email}, ip={client_ip}")

    # Return empty response to remove the element from DOM
    return Response(content="", status_code=200)


@router.put("/items/{item_id}", response_class=HTMLResponse)
async def update_item(
    request: Request,
    item_id: int,
    title: str = Form(...),
    content: Optional[str] = Form(None),
    is_public: bool = Form(False),
    csrf: str = Form(...),
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Update an item via HTMX form"""
    client_ip = get_client_ip(request)

    # Verify CSRF token
    try:
        verify_csrf(request, csrf)
    except Exception as e:
        logger.error(f"CSRF validation failed on item update: user={current_user.email}, ip={client_ip}")
        return templates.TemplateResponse(
            "fragments/item_error.html",
            {"request": request, "error": "Security validation failed. Please refresh."}
        )

    # Get the item
    item = session.get(Item, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.user_id != current_user.id:
        logger.warning(f"Unauthorized update attempt: user={current_user.email}, item_id={item_id}, ip={client_ip}")
        raise HTTPException(status_code=403, detail="Not authorized to update this item")

    # Update item
    item.title = title.strip()
    item.content = content.strip() if content else None
    item.is_public = is_public
    item.updated_at = datetime.now(timezone.utc)

    session.add(item)
    session.commit()
    session.refresh(item)

    logger.info(f"Item updated: id={item_id}, user={current_user.email}, ip={client_ip}")

    return templates.TemplateResponse(
        "fragments/item_card.html",
        {"request": request, "item": item}
    )


# ============== JSON API Endpoints ==============

@router.get("/api/items", response_model=ItemListResponse)
async def list_items_api(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Get user's items as JSON (API endpoint)"""
    offset = (page - 1) * per_page

    # Get total count
    total = session.exec(
        select(func.count(Item.id)).where(Item.user_id == current_user.id)
    ).one()

    # Get items
    items = session.exec(
        select(Item)
        .where(Item.user_id == current_user.id)
        .order_by(Item.created_at.desc())
        .offset(offset)
        .limit(per_page)
    ).all()

    return ItemListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page
    )


@router.post("/api/items", response_model=ItemResponse, status_code=201)
async def create_item_api(
    item_data: ItemCreate,
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Create a new item via JSON API"""
    item = Item(
        user_id=current_user.id,
        title=item_data.title,
        content=item_data.content,
        is_public=item_data.is_public,
    )

    session.add(item)
    session.commit()
    session.refresh(item)

    logger.info(f"Item created via API: id={item.id}, user={current_user.email}")

    return item


@router.get("/api/items/{item_id}", response_model=ItemResponse)
async def get_item_api(
    item_id: int,
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Get a single item by ID"""
    item = session.get(Item, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Allow access if user owns it or it's public
    if item.user_id != current_user.id and not item.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to view this item")

    return item


@router.delete("/api/items/{item_id}", status_code=204)
async def delete_item_api(
    item_id: int,
    current_user: User = Depends(manager),
    session: Session = Depends(get_session)
):
    """Delete an item via JSON API"""
    item = session.get(Item, item_id)

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this item")

    session.delete(item)
    session.commit()

    logger.info(f"Item deleted via API: id={item_id}, user={current_user.email}")

