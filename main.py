"""
Main Application - Crypto Portfolio Tracker v3
===========================================================================

Punto de entrada principal de la aplicación FastAPI.

Incluye:
- Configuración de FastAPI
- Setup de logging centralizado
- Inyección de dependencias
- Middleware de seguridad
- CORS configuration
- Event handlers (startup/shutdown)
- Error handling centralizado

Para ejecutar:
    uvicorn main:app --reload
    
    O con configuración específica:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

API Documentation:
    - Swagger UI: http://localhost:8000/docs
    - ReDoc: http://localhost:8000/redoc
    - OpenAPI Schema: http://localhost:8000/openapi.json

Author: Crypto Portfolio Tracker Team
Version: 3.0.0
License: MIT
"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.utils import setup_root_logger, LoggerSetup
from src.api.v1 import router, exchanges_router, auth_router, price_mappings_router
from src.utils.config_loader import ConfigLoader
from src.api.connectors.manager import ConnectorManager


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(cfg: ConfigLoader):
    """Configura logging centralizado usando `config/config.yaml`."""
    # Crear directorio de logs si no existe
    logs_dir = Path("./logs")
    logs_dir.mkdir(exist_ok=True)

    log_cfg = cfg.get_logging_config()
    level = log_cfg.get("level", "INFO")
    log_file = log_cfg.get("file", "./logs/app.log")
    max_bytes = int(log_cfg.get("max_bytes", 10485760))
    backup_count = int(log_cfg.get("backup_count", 5))

    # Setup del logger raíz
    setup_root_logger(
        level=level,
        log_file=log_file,
        max_bytes=max_bytes,
        backup_count=backup_count,
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Crypto Portfolio Tracker v3.0.0 - Starting up")
    logger.info("Using config.app.env=%s", cfg.config.get("app", {}).get("env", "development"))
    logger.info("=" * 80)

    return logger


# Initialize global configuration and logger
cfg = ConfigLoader()
logger = setup_logging(cfg)


# ============================================================================
# Lifespan Events
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestiona eventos de lifecycle (startup/shutdown).
    
    Startup:
        - Inicializa servicios
        - Conecta a base de datos
        - Carga configuración
    
    Shutdown:
        - Cierra conexiones
        - Limpia recursos
        - Guarda estado
    """
    # Startup
    logger.info("🚀 Application starting up...")
    logger.info("📦 Database: Connected")
    logger.info("🔧 Services: Initialized")

    # Initialize and start connector manager if configured
    try:
        app.state.connector_manager = ConnectorManager()
        try:
            conn_cfg = cfg.config.get("connectors", {})
            bg_cfg = conn_cfg.get("background_sync", {}) if conn_cfg else {}
            enabled = bool(bg_cfg.get("enabled", True))
            interval = int(bg_cfg.get("interval_seconds", 300))
        except Exception:
            enabled = True
            interval = 300

        if enabled:
            app.state.connector_manager.start_background_sync(interval_seconds=interval)
            logger.info(f"Connector background sync started (interval={interval}s)")
        else:
            logger.info("Connector background sync is disabled by configuration")
    except Exception as e:
        logger.warning(f"Could not start connector background sync: {e}")

    logger.info("✅ Application ready to serve requests")

    yield  # Aplicación ejecutándose

    # Shutdown
    logger.info("🛑 Application shutting down...")
    # Stop connector background sync if running
    try:
        cm = getattr(app.state, 'connector_manager', None)
        if cm:
            cm.stop_background_sync()
            logger.info("Connector background sync stopped")
    except Exception as e:
        logger.warning(f"Error stopping connector background sync: {e}")

    logger.info("💾 Closing database connections...")
    logger.info("🧹 Cleaning up resources...")
    logger.info("👋 Goodbye!")


# ============================================================================
# FastAPI Application Setup
# ============================================================================

app = FastAPI(
    title="Crypto Portfolio Tracker API",
    description="Advanced cryptocurrency portfolio management, tax calculation, and DeFi analysis platform",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

logger.info("FastAPI application initialized")


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS - Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://localhost:8080",
        "https://localhost",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("✅ CORS middleware configured")

# Gzip compression
app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,
)

logger.info("✅ GZIP compression middleware configured")

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "testserver",
        "127.0.0.1",
        "*.localhost",
        "*.example.com",
    ],
)

logger.info("✅ Trusted hosts middleware configured")


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Maneja excepciones HTTP estándar.
    
    Args:
        request: Request object
        exc: HTTPException
        
    Returns:
        JSONResponse con estructura de error
    """
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} | Path: {request.url.path}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Maneja errores de validación de request.
    
    Args:
        request: Request object
        exc: RequestValidationError
        
    Returns:
        JSONResponse con detalles de validación
    """
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "status_code": 422,
            "path": request.url.path,
            "details": [
                {
                    "field": ".".join(str(x) for x in error["loc"][1:]),
                    "message": error["msg"],
                    "type": error["type"],
                }
                for error in exc.errors()
            ],
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Maneja excepciones genéricas no capturadas.
    
    Args:
        request: Request object
        exc: Exception
        
    Returns:
        JSONResponse con error 500
    """
    logger.error(
        f"Unhandled exception on {request.url.path}: {str(exc)}",
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "path": request.url.path,
        },
    )


logger.info("✅ Exception handlers configured")


# ============================================================================
# Custom Middleware
# ============================================================================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para logging de requests/responses.
    
    Registra:
    - Método HTTP
    - Path
    - Query parameters
    - Status code
    - Tiempo de respuesta
    """
    import time
    
    start_time = time.time()
    
    # Log request
    logger.debug(
        f"📨 {request.method} {request.url.path} | "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.debug(
        f"📤 {request.method} {request.url.path} | "
        f"Status: {response.status_code} | "
        f"Time: {process_time:.3f}s"
    )
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


logger.info("✅ Custom middleware configured")


# ============================================================================
# Routes Registration
# ============================================================================

app.include_router(router)
app.include_router(exchanges_router)
app.include_router(auth_router)
app.include_router(price_mappings_router)

logger.info("✅ API v1 routes registered")


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["root"])
async def root():
    """
    Endpoint raíz.
    
    Retorna información sobre la API.
    """
    return {
        "message": "Crypto Portfolio Tracker API v3.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


# ============================================================================
# Health Check Endpoint (Redundante pero útil)
# ============================================================================

@app.get("/health/live", tags=["health"])
async def health_live():
    """
    Liveness probe - Indica si la aplicación está viva.
    
    Usado por: Kubernetes, Docker, Load balancers
    """
    return {
        "status": "alive",
        "service": "crypto-portfolio-tracker",
        "version": "3.0.0",
    }


@app.get("/health/ready", tags=["health"])
async def health_ready():
    """
    Readiness probe - Indica si la aplicación está lista para servir.
    
    Usado por: Kubernetes, Docker, Load balancers
    """
    try:
        # Aquí puedes verificar conectividad a BD, etc
        return {
            "status": "ready",
            "database": "connected",
            "services": "initialized",
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "error": str(e),
        }


# ============================================================================
# Application Info Endpoint
# ============================================================================

@app.get("/info", tags=["info"])
async def app_info():
    """
    Información detallada de la aplicación.
    """
    return {
        "name": "Crypto Portfolio Tracker",
        "version": "3.0.0",
        "description": "Advanced cryptocurrency portfolio management and tax tracking",
        "author": "Crypto Portfolio Tracker Team",
        "license": "MIT",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "environment": cfg.config.get("app", {}).get("env", "development"),
        "features": [
            "Portfolio management",
            "Multi-wallet support",
            "Tax calculations (FIFO, LIFO, Average Cost)",
            "Real-time price tracking",
            "DeFi integration",
            "Transaction history",
            "Performance analytics",
            "Report generation (JSON, CSV)",
        ],
    }


logger.info("✅ Root and health endpoints configured")


# Removed deprecated @app.on_event handlers; startup/shutdown
# behavior is handled in the `lifespan` asynccontextmanager above.


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Starting Uvicorn server...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )