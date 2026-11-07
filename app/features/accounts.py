"""HTML and REST account routes backed by the prepared security helpers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app import security
from app.schemas import LoginInput, PublicUser, SignupInput

router = APIRouter()
CsrfHeader = Annotated[str | None, Header()]
AuthenticatedUser = Annotated[dict[str, str], Depends(security.require_user)]


def _signup(request, credentials):
    security.limit_signup(request)
    return security.signup(
        request.app.state.settings, credentials.username, credentials.password
    )


def _login(request, response, credentials):
    return security.login(request, response, credentials.username, credentials.password)


@router.get("/api/csrf")
def api_csrf(request: Request, response: Response):
    """Return a token tied to the current browser session."""
    return {"csrf_token": security.csrf_token(request, response)}


@router.post("/api/signup", response_model=PublicUser, status_code=201)
def api_signup(
    request: Request, credentials: SignupInput, x_csrf_token: CsrfHeader = None
):
    """Register a member using validated credentials."""
    security.require_csrf(request, x_csrf_token)
    return _signup(request, credentials)


@router.post("/api/login", response_model=PublicUser)
def api_login(
    request: Request,
    response: Response,
    credentials: LoginInput,
    x_csrf_token: CsrfHeader = None,
):
    """Start a signed session and return public identity."""
    security.require_csrf(request, x_csrf_token)
    return _login(request, response, credentials)


@router.get("/api/me", response_model=PublicUser)
def api_me(user: AuthenticatedUser):
    """Return public identity from a live session."""
    return user


@router.post("/api/logout")
def api_logout(request: Request, response: Response, x_csrf_token: CsrfHeader = None):
    """Revoke the session after checking its CSRF token."""
    security.require_csrf(request, x_csrf_token)
    security.logout(request, response)
    return {"status": "logged_out"}


def _csrf_page(request, template, context, error=None):
    cookie_response = Response(headers=error.headers if error else None)
    context["csrf_token"] = security.csrf_token(request, cookie_response)
    response = request.app.state.templates.TemplateResponse(
        request=request,
        name=template,
        context=context,
        status_code=error.status_code if error else 200,
    )
    for name, value in cookie_response.headers.items():
        if name != "content-length":
            response.headers.append(name, value)
    return response


def _form(request, action, username="", error=None):
    return _csrf_page(
        request,
        "account.html",
        {
            "action": action,
            "username": username,
            "error": error.detail if error else None,
        },
        error,
    )


async def _fields(request: Request):
    async with request.form(max_files=0, max_fields=4) as form:
        if len(form.multi_items()) != len(form):
            raise HTTPException(422, "Send each form field once.")
        return dict(form)


FormFields = Annotated[dict, Depends(_fields)]


def _submit(request, fields, action):
    username = ""
    try:
        security.require_csrf(request, fields.pop("csrf_token", None))
        model = SignupInput if action == "signup" else LoginInput
        credentials = model.model_validate(fields)
        username = credentials.username
        if action == "signup":
            _signup(request, credentials)
            return RedirectResponse("/login?registered=1", status_code=303)
        response = RedirectResponse("/dashboard", status_code=303)
        _login(request, response, credentials)
        return response
    except ValidationError:
        error = HTTPException(422, "Check your username and password and try again.")
    except HTTPException as failure:
        error = failure
    return _form(request, action, username, error)


@router.get("/signup", include_in_schema=False)
def signup_page(request: Request):
    """Show the registration form."""
    return _form(request, "signup")


@router.post("/signup", include_in_schema=False)
def signup_form(request: Request, fields: FormFields):
    """Register through the shared account service."""
    return _submit(request, fields, "signup")


@router.get("/login", include_in_schema=False)
def login_page(request: Request):
    """Show the login form."""
    return _form(request, "login")


@router.post("/login", include_in_schema=False)
def login_form(request: Request, fields: FormFields):
    """Log in through the shared account service."""
    return _submit(request, fields, "login")


@router.get("/dashboard", include_in_schema=False)
def dashboard(request: Request):
    """Require a live session before rendering the member dashboard."""
    user = security.authenticate(request)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    return _csrf_page(request, "dashboard.html", {"user": user})


@router.post("/logout", include_in_schema=False)
def logout_form(request: Request, fields: FormFields):
    """Revoke the browser session and return to the homepage."""
    security.require_csrf(request, fields.get("csrf_token"))
    response = RedirectResponse("/", status_code=303)
    security.logout(request, response)
    return response
