import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.limiter import limiter
from app.routes import auth_routes, student_routes, institution_routes, user_routes, attendance_routes, survey_routes, analytics_routes, subscription_routes, me_routes, assigned_survey_routes
from app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="School Wellness Intelligence Platform",
    description="Multi-tenant student management system with RBAC, Attendance, Surveys, and Analytics.",
    version="1.4.0",
    # Disable interactive docs in production — prevents API enumeration
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.is_production:
        # Tells browsers: only ever access this domain over HTTPS for the next year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )

# All routes under /api/v1
V1 = "/api/v1"
app.include_router(auth_routes.router,         prefix=V1)
app.include_router(student_routes.router,      prefix=V1)
app.include_router(institution_routes.router,  prefix=V1)
app.include_router(user_routes.router,         prefix=V1)
app.include_router(attendance_routes.router,   prefix=V1)
app.include_router(survey_routes.router,       prefix=V1)
app.include_router(analytics_routes.router,    prefix=V1)
app.include_router(subscription_routes.router,    prefix=V1)
app.include_router(me_routes.router,              prefix=V1)
app.include_router(assigned_survey_routes.router, prefix=V1)

@app.get("/")
async def root():
    return {"message": "School Wellness Intelligence Platform API", "version": "1.4.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}
