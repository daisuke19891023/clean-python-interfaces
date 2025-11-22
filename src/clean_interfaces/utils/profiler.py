"""Lightweight function profiling utilities.

Provides a decorator to record execution time and optional memory metrics,
with activation controlled by settings/environment. Designed to integrate
with the project's structured logging and tolerate missing optional deps.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

import structlog
from clean_interfaces.utils.settings import get_settings


F = TypeVar("F", bound=Callable[..., Any])


def _get_rss_mb() -> float | None:
    """Get current process RSS in megabytes.

    Tries psutil when available, falls back to resource on POSIX systems.
    Returns None if neither method is available.
    """
    # Try psutil first
    try:
        import psutil  # type: ignore[import-not-found]

        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        pass

    # Fallback to resource (POSIX)
    try:
        import resource  # type: ignore[import-not-found]

        usage = resource.getrusage(resource.RUSAGE_SELF)
        # On Linux, ru_maxrss is in kilobytes
        rss_kb = float(usage.ru_maxrss)
        return rss_kb / 1024.0
    except Exception:
        return None


def _maybe_start_tracemalloc() -> bool:
    """Start tracemalloc if not already started. Return True if started now."""
    try:
        import tracemalloc

        if not tracemalloc.is_tracing():
            tracemalloc.start()
            return True
    except Exception:
        return False
    return False


def _get_tracemalloc_stats() -> tuple[int, int] | None:
    """Return (allocated_bytes, peak_bytes) since start, or None on error."""
    try:
        import tracemalloc

        current, peak = tracemalloc.get_traced_memory()
        return int(current), int(peak)
    except Exception:
        return None


def _stop_tracemalloc_if_started(started_here: bool) -> None:
    if not started_here:
        return
    try:
        import tracemalloc

        tracemalloc.stop()
    except Exception:
        pass


def _maybe_start_span(create_span: bool, span_name: str):  # type: ignore[override]
    """Start an OpenTelemetry span if requested and otel is available.

    Returns a context manager. If OTEL is not available, returns a no-op context manager.
    """
    if not create_span:
        # Simple no-op context manager
        from contextlib import nullcontext

        return nullcontext()

    try:
        from opentelemetry import trace  # type: ignore[import-untyped]

        tracer = trace.get_tracer("clean_interfaces.profiler")  # type: ignore[attr-defined]
        return tracer.start_as_current_span(span_name)
    except Exception:
        from contextlib import nullcontext

        return nullcontext()


def profile(
    logger: Any | None = None,
    *,
    record_memory: bool | None = None,
    create_span: bool | None = None,
    name: str | None = None,
) -> Callable[[F], F]:
    """Decorator to record execution time and optional memory metrics.

    Args:
        logger: Logger to use. If None, a module-based structlog logger is used.
        record_memory: Force memory metrics on/off. If None, follows settings.
        create_span: Create an OTEL span. If None, follows settings.
        name: Optional operation name for spans; defaults to function name.

    Returns:
        Decorator function.
    """

    settings = get_settings()

    def decorator(func: F) -> F:
        op_name = name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            active_memory = (
                settings.profiler_active and settings.profiler_collect_memory
                if record_memory is None
                else record_memory
            )
            active_span = (
                settings.profiler_active and settings.profiler_create_spans
                if create_span is None
                else create_span
            )

            bound_logger = logger if logger is not None else structlog.get_logger(func.__module__)

            # Time measurement
            start_time = time.perf_counter()

            # Memory measurement
            rss_before = _get_rss_mb() if active_memory else None
            started_tracemalloc = _maybe_start_tracemalloc() if active_memory else False

            span_cm = _maybe_start_span(active_span, f"profile:{op_name}")
            exception_info: str | None = None
            try:
                with span_cm:
                    return func(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001 - want broad capture for logging
                exception_info = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                end_time = time.perf_counter()
                duration_ms = (end_time - start_time) * 1000.0

                log_data: dict[str, Any] = {
                    "function_name": func.__name__,
                    "duration_ms": round(duration_ms, 3),
                }

                if active_memory:
                    rss_after = _get_rss_mb()
                    tm_stats = _get_tracemalloc_stats()
                    if rss_after is not None:
                        log_data["rss_mb"] = round(float(rss_after), 3)
                    if rss_before is not None and rss_after is not None:
                        log_data["rss_delta_mb"] = round(float(rss_after - rss_before), 3)
                    if tm_stats is not None:
                        current_b, peak_b = tm_stats
                        log_data["py_allocated_kb"] = round(current_b / 1024.0, 3)
                        log_data["py_peak_kb"] = round(peak_b / 1024.0, 3)

                _stop_tracemalloc_if_started(started_tracemalloc)

                if exception_info is not None:
                    log_data["exception"] = exception_info
                    bound_logger.error("Function execution failed", **log_data)
                else:
                    bound_logger.info("Function execution completed", **log_data)

        return wrapper  # type: ignore[return-value]

    return decorator

