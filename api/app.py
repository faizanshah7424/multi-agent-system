from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from config import settings
from core.logging import get_logger

logger = get_logger("API_App")


def create_app() -> FastAPI:
    """
    FastAPI Application Factory.
    Configures server settings, registers routers, and sets up middleware.
    """
    from core.di_setup import bootstrap_di

    bootstrap_di()

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(
            "Task queue system initialized in multi-process decoupled mode. FastAPI will only write/read tasks to SQLite."
        )
        yield
        logger.info("FastAPI shut down complete.")

    from core.diagnostics.version import VersionManager

    v_mgr = VersionManager()

    app = FastAPI(
        title="CodeOrbit AI API",
        description=(
            "FastAPI backend facilitating task plans, agent executions, logs "
            "tracking, and state memory persistence for CodeOrbit AI via Gemini API."
        ),
        version=v_mgr.version,
        lifespan=lifespan,
    )

    # Enable CORS for external developer panels or frontends
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # In-memory rate limiting state
    from collections import defaultdict

    client_requests = defaultdict(list)
    RATE_LIMIT_WINDOW = 60  # seconds
    RATE_LIMIT_MAX_REQUESTS = 100  # requests per window
    MAX_PAYLOAD_SIZE = 10 * 1024 * 1024  # 10MB

    # Register HTTP middleware for logging correlation and performance metrics
    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        import uuid
        import time
        from fastapi.responses import JSONResponse
        from core.logging import set_correlation_context
        from core.metrics import metrics_collector

        # 1. Enforce Payload Size Limit (413 Content Too Large)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_PAYLOAD_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request payload too large. Maximum size allowed is 10MB."
                        },
                    )
            except ValueError:
                pass

        # Intercept bodies if method is write-based to prevent payload limit bypass
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                body = await request.body()
                if len(body) > MAX_PAYLOAD_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request payload too large. Maximum size allowed is 10MB."
                        },
                    )
            except Exception as e:
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"Error reading request payload: {str(e)}"},
                )

        # 2. Enforce IP-based Rate Limiting (429 Too Many Requests)
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Clean older requests from bucket
        client_requests[client_ip] = [
            t for t in client_requests[client_ip] if now - t < RATE_LIMIT_WINDOW
        ]

        # Periodic cleanup of client_requests dict to prevent memory leak of inactive IPs
        if len(client_requests) > 1000:
            inactive_ips = [
                ip
                for ip, reqs in client_requests.items()
                if not any(now - t < RATE_LIMIT_WINDOW for t in reqs)
            ]
            for ip in inactive_ips:
                del client_requests[ip]

        if len(client_requests[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )
        client_requests[client_ip].append(now)

        # 3. Resolve trace and session correlation keys
        request_id = request.headers.get("x-request-id", f"req_{uuid.uuid4().hex[:8]}")
        session_id = request.query_params.get("session_id", "N/A")
        if session_id == "N/A":
            session_id = request.headers.get("x-session-id", "N/A")

        # Extract task_id from path if request is under /tasks/{task_id}
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0] == "tasks":
            session_id = path_parts[1]

        # 2. Configure logging context
        set_correlation_context(
            task_id=session_id,
            workflow_id=session_id,
            agent_name="api",
            execution_id=request_id,
            request_id=request_id,
            session_id=session_id,
        )

        # 3. Track request and latency
        metrics_collector.record_request()
        start_time = time.time()
        try:
            response = await call_next(request)
            duration_s = time.time() - start_time
            metrics_collector.record_request_duration(duration_s)
            response.headers["x-request-id"] = request_id
            response.headers["x-session-id"] = session_id
            return response
        except Exception as e:
            duration_s = time.time() - start_time
            metrics_collector.record_request_duration(duration_s)
            metrics_collector.record_failure()
            raise e

    # Register endpoints router
    from api.auth_routes import router as auth_router
    from api.admin_routes import router as admin_router
    from api.notification_routes import router as notification_router
    from api.hospital_routes import router as hospital_router

    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(notification_router)
    app.include_router(hospital_router)
    app.include_router(api_router)

    @app.get("/")
    def read_root() -> dict:
        """Root API health check and environment status endpoint."""
        from core.diagnostics.version import VersionManager

        v_mgr = VersionManager()
        return {
            "name": "CodeOrbit AI API",
            "status": "online",
            "version": v_mgr.version,
            "default_model": settings.default_model,
            "persist_directory": str(settings.persist_path.resolve()),
        }

    logger.info("FastAPI application instance created successfully.")
    return app


# Main app instance
app = create_app()
