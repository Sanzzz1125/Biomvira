import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import settings
from app import keep_awake
from app.migrate import run_migrations


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.auto_migrate:
        run_migrations()
    pinger = keep_awake.start()
    yield
    if pinger:
        pinger.cancel()


app = FastAPI(
    title=settings.app_name + " API",
    description="Evidence-grounded Nutrition Support Platform analyzing laboratory biomarkers for personalized Indian dietary recommendations.",
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS is only for local tooling; production traffic is same-origin through Vercel's /api rewrite.
_origins = settings.get_allowed_origins_list()
if _origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials="*" not in _origins,  # never send cookies to arbitrary origins
        allow_methods=["*"],
        allow_headers=["*"],
    )

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
PRIVATE_PREFIXES = ("/api/v1/auth", "/api/v1/history", "/api/v1/admin")


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # CSRF (double-submit): signed-in requests that change data must echo the CSRF cookie.
    if (request.method in UNSAFE_METHODS and request.url.path.startswith("/api/")
            and request.cookies.get(settings.session_cookie_name)):
        cookie = request.cookies.get(settings.csrf_cookie_name, "").encode()
        header = request.headers.get("x-csrf-token", "").encode()
        if not cookie or not secrets.compare_digest(cookie, header):
            return JSONResponse({"detail": "Security check failed. Refresh the page and try again."},
                                status_code=403)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "same-origin")
    if request.url.path.startswith(PRIVATE_PREFIXES):
        response.headers["Cache-Control"] = "no-store"
    return response


# Mount API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/api/health")
def health():
    # Deliberately does not touch the database, so uptime checks never wake Neon.
    return {
        "project": settings.app_name,
        "tagline": "From laboratory insights to personalized nutrition",
        "version": settings.app_version,
        "status": "online",
        "docs_url": "/docs",
    }

# Local all-in-one mode: serve the built frontend when it exists (production uses Vercel).
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.exists(FRONTEND_DIST):
    assets_dir = os.path.join(FRONTEND_DIST, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        # API misses must not become successful HTML responses. Resolve paths before
        # serving files so encoded traversal cannot expose private files.
        if full_path == 'api' or full_path.startswith('api/'):
            raise HTTPException(404, 'Not found')
        root = Path(FRONTEND_DIST).resolve()
        target_file = (root / full_path).resolve()
        if not target_file.is_relative_to(root):
            raise HTTPException(404, 'Not found')
        if full_path and target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "project": settings.app_name,
            "tagline": "From laboratory insights to personalized nutrition",
            "version": settings.app_version,
            "status": "online",
            "docs_url": "/docs",
        }
