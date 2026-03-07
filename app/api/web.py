"""Web routes: serve HTML pages (Jinja2)."""
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/alerts", response_class=HTMLResponse)
def alerts_page(request: Request):
    return templates.TemplateResponse("alerts.html", {"request": request})


@router.get("/report", response_class=HTMLResponse)
def report_page(request: Request):
    return templates.TemplateResponse("report.html", {"request": request})


@router.get("/incidents", response_class=HTMLResponse)
def incidents_list_page(request: Request):
    return templates.TemplateResponse("incidents.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


@router.get("/broadcast", response_class=HTMLResponse)
def broadcast_page(request: Request):
    return templates.TemplateResponse("broadcast.html", {"request": request})


@router.get("/logout")
def logout():
    return RedirectResponse(url="/", status_code=302)
