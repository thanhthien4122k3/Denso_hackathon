"""Khởi tạo FastAPI: lifespan (migration), exception handlers, static và routes."""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from app.auth import auth_middleware
from app.engine.rules import load_rules
from app.exceptions import (
    DatabaseUnavailableError,
    DuplicateCodeError,
    NotFoundError,
    RecordConflictError,
    ValidationFailedError,
)
from app.graph import EdgeValidationError
from app.migrations import run_migrations
from app.query_loader import load_all
from app.repositories.production_repository import ProductionRepository
from app.routers import (
    analysis,
    auth,
    catalog,
    context,
    dashboard,
    graph,
    health,
    incidents,
    operations,
    production,
    scenarios,
    system,
    tasks,
)
from app.settings import STATIC_DIR, ConfigError, get_settings

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # pragma: no cover
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("denso")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        settings = get_settings()
    except ConfigError as exc:
        logger.error("Cấu hình không hợp lệ: %s", exc)
        raise

    logger.info(
        "Kết nối database %s@%s:%s/%s ...",
        settings.db_user,
        settings.db_host,
        settings.db_port,
        settings.db_name,
    )
    try:
        load_all()
        load_rules()
        ProductionRepository().init_schema()
        applied = run_migrations()
        if applied:
            logger.info("Đã áp dụng migration: %s", ", ".join(applied))
    except Exception as exc:
        logger.error("Không thể khởi tạo cơ sở dữ liệu: %s", exc)
        raise RuntimeError(
            "Không thể kết nối/khởi tạo PostgreSQL hoặc migration thất bại. "
            "Hãy kiểm tra file .env và trạng thái dịch vụ PostgreSQL."
        ) from exc

    logger.info("Ứng dụng đã sẵn sàng.")
    yield
    logger.info("Ứng dụng dừng.")


app = FastAPI(
    title="Denso D3 - Liên kết chuỗi sản xuất và phân tích sự cố",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,
)

app.middleware("http")(auth_middleware)


@app.exception_handler(DatabaseUnavailableError)
async def database_unavailable_handler(request: Request, exc: DatabaseUnavailableError):
    logger.error("Database không sẵn sàng: %s", exc)
    return JSONResponse(
        status_code=503,
        content={"success": False,
                 "message": "Cơ sở dữ liệu không sẵn sàng. Vui lòng thử lại sau.", "data": None},
    )


@app.exception_handler(RecordConflictError)
async def record_conflict_handler(request: Request, exc: RecordConflictError):
    return JSONResponse(status_code=409, content={"success": False, "message": str(exc), "data": None})


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"success": False, "message": str(exc), "data": None})


@app.exception_handler(DuplicateCodeError)
async def duplicate_code_handler(request: Request, exc: DuplicateCodeError):
    return JSONResponse(status_code=409, content={"success": False,
                                                  "message": "Mã đã tồn tại.", "data": None})


@app.exception_handler(EdgeValidationError)
async def edge_validation_handler(request: Request, exc: EdgeValidationError):
    return JSONResponse(status_code=422, content={"success": False, "message": str(exc), "data": None})


@app.exception_handler(ValidationFailedError)
async def validation_failed_handler(request: Request, exc: ValidationFailedError):
    return JSONResponse(status_code=422, content={"success": False, "message": str(exc), "data": None})


app.include_router(auth.router)
app.include_router(production.router)
app.include_router(health.router)
app.include_router(dashboard.router)
app.include_router(catalog.router)
app.include_router(system.router)
app.include_router(graph.router)
app.include_router(operations.router)
app.include_router(incidents.router)
app.include_router(analysis.router)
app.include_router(tasks.router)
app.include_router(context.router)
app.include_router(scenarios.scenarios_router)
app.include_router(scenarios.survey_router)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)
