"""Protected browser and REST views use the same current-role dependency."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app import security

router = APIRouter()


@router.get("/api/admin")
def api_admin(user: Annotated[dict[str, str], Depends(security.require_admin)]):
    """Return administration status to an authorized administrator."""
    return {"status": "ready", "administrator": user["username"]}


@router.get("/admin", include_in_schema=False)
def admin_page(request: Request):
    """Redirect anonymous visitors and show a 403 page to signed-in members."""
    try:
        user = security.require_admin(request)
    except HTTPException as error:
        if error.status_code == 401:
            return RedirectResponse("/login", status_code=303)
        if error.status_code != 403:
            raise
        return request.app.state.templates.TemplateResponse(
            request=request, name="admin.html", context={"user": None}, status_code=403
        )
    return request.app.state.templates.TemplateResponse(
        request=request, name="admin.html", context={"user": user}
    )
