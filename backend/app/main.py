import logging
from contextlib import asynccontextmanager

import logfire
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from app.auth.api.login import anon_router as auth_anon_router
from app.auth.api.users import router as users_router
from app.auth.jwt import auth_user
from app.auth.permissions import Permission
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.core.logging import configure_logfire, configure_logging
from app.core.sentry import init_sentry
from app.members.api.members import router as members_router
from app.members.api.signup import anon_router as members_signup_router

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables (tests), register Celery tasks, init observability."""
    logger.info('Starting up rosetta...')
    create_db_and_tables()
    logger.info('Database tables created')

    # Celery task modules are imported here once domain tasks exist, so the registry is populated.

    init_sentry()

    if settings.logfire_token:
        configure_logfire()
        logfire.instrument_fastapi(app)

    yield

    logger.info('Shutting down rosetta...')


app = FastAPI(title='rosetta', version='0.1.0', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.allowed_origins.split(','),
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allow_headers=['Authorization', 'Content-Type', 'Accept', 'Origin', 'X-Requested-With'],
)


@app.get('/scalar', include_in_schema=False)
async def scalar_docs() -> HTMLResponse:
    """Serve the Scalar API reference for the API."""
    return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)


@app.get('/', name='health', dependencies=[Depends(Permission.anonymous)])
async def health() -> dict:
    """Unauthenticated healthcheck."""
    return {'status': 'healthy'}


# -------------------------------------------------------------------
# 'auth' routers (anonymous)
# -------------------------------------------------------------------
app.include_router(auth_anon_router, dependencies=[Depends(Permission.anonymous)])
# Public self-service member signup (creates a User(MEMBER) with a real password + profile).
app.include_router(members_signup_router, dependencies=[Depends(Permission.anonymous)])


# -------------------------------------------------------------------
# Authenticated routers
# -------------------------------------------------------------------
app.include_router(users_router, dependencies=[Depends(auth_user)])

# Member admin is staff-only — every route requires an admin (Permission.is_admin authenticates too).
app.include_router(members_router, dependencies=[Depends(Permission.is_admin)])


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('app.main:app', host=settings.host, port=settings.port, reload=True)
