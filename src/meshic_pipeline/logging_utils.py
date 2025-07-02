"""
Standardized logging utilities for the Suhail Pipeline.

This module provides:
- Centralized logging configuration
- Structured logging with context
- Performance monitoring
- Error correlation
"""

from __future__ import annotations

import logging
import logging.config
import logging.handlers
import sys
import time
import asyncio
import threading
import queue
import random
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional, Callable, TypeVar, Union
from datetime import datetime
import json
import weakref
from collections import deque

from .config import settings
from .exceptions import ErrorContext, get_error_handler

F = TypeVar('F', bound=Callable[..., Any])


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Start with the basic log record
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'error_details'):
            log_entry["error_details"] = record.error_details
        
        if hasattr(record, 'performance_metrics'):
            log_entry["performance_metrics"] = record.performance_metrics
        
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        
        if hasattr(record, 'correlation_id'):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Return JSON formatted string for structured logging
        if settings.environment.value in ["production", "staging"]:
            return json.dumps(log_entry, default=str)
        else:
            # Human-readable format for development
            base_msg = f"{log_entry['timestamp']} - {log_entry['logger']} - {log_entry['level']} - {log_entry['message']}"
            if 'error_details' in log_entry:
                base_msg += f"\nError Details: {json.dumps(log_entry['error_details'], indent=2, default=str)}"
            if 'performance_metrics' in log_entry:
                base_msg += f"\nPerformance: {log_entry['performance_metrics']}"
            return base_msg


class AsyncLogHandler(logging.Handler):
    """Asynchronous log handler for improved performance."""
    
    def __init__(self, target_handler: logging.Handler, max_queue_size: int = 10000):
        super().__init__()
        self.target_handler = target_handler
        self.log_queue = queue.Queue(maxsize=max_queue_size)
        self.worker_thread = None
        self._stop_event = threading.Event()
        self._start_worker()
    
    def _start_worker(self):
        """Start the background worker thread."""
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def _worker(self):
        """Background worker that processes log records."""
        while not self._stop_event.is_set():
            try:
                # Get record with timeout
                record = self.log_queue.get(timeout=1.0)
                if record is None:  # Sentinel value to stop
                    break
                
                # Process the record
                self.target_handler.emit(record)
                self.log_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                # Log to stderr to avoid infinite recursion
                print(f"Error in async log worker: {e}", file=sys.stderr)
    
    def emit(self, record: logging.LogRecord):
        """Emit a log record asynchronously."""
        try:
            # Apply log sampling if configured
            if settings.logging_optimization_config.log_sampling_rate < 1.0:
                if random.random() > settings.logging_optimization_config.log_sampling_rate:
                    return
            
            self.log_queue.put_nowait(record)
        except queue.Full:
            # Queue is full, drop the log record
            pass
    
    def close(self):
        """Close the handler and stop the worker thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            # Signal stop and wait for worker to finish
            self._stop_event.set()
            self.log_queue.put(None)  # Sentinel
            self.worker_thread.join(timeout=5.0)
        
        self.target_handler.close()
        super().close()


class OptimizedMemoryHandler(logging.handlers.MemoryHandler):
    """Memory handler optimized for batch processing."""
    
    def __init__(self, capacity: int, target: logging.Handler):
        super().__init__(capacity, target=target)
        self.buffer_lock = threading.Lock()
    
    def shouldFlush(self, record: logging.LogRecord) -> bool:
        """Determine if buffer should be flushed."""
        # Flush on error/critical levels or when buffer is full
        return (
            record.levelno >= logging.ERROR or 
            len(self.buffer) >= self.capacity
        )
    
    def emit(self, record: logging.LogRecord):
        """Emit a record with thread safety."""
        with self.buffer_lock:
            super().emit(record)


class PerformanceLogger:
    """Logger for performance monitoring and metrics with memory optimization."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._operation_times: deque = deque(maxlen=settings.memory_config.max_cached_objects)
        self._lock = threading.Lock()
    
    @contextmanager
    def time_operation(self, operation: str, **context):
        """Context manager for timing operations with memory optimization."""
        start_time = time.perf_counter()
        
        # Only log start message if not in production or if debug enabled
        if not settings.is_production() or settings.debug:
            self.logger.info(
                f"Starting operation: {operation}",
                extra={"context": context, "operation": operation}
            )
        
        try:
            yield
            duration = time.perf_counter() - start_time
            
            # Store operation time in memory-efficient way
            with self._lock:
                self._operation_times.append({
                    "operation": operation,
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "status": "success"
                })
            
            self.logger.info(
                f"Completed operation: {operation}",
                extra={
                    "performance_metrics": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "status": "success"
                    },
                    "context": context
                }
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            
            # Store failed operation
            with self._lock:
                self._operation_times.append({
                    "operation": operation,
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "status": "failed",
                    "error": str(e)
                })
            
            self.logger.error(
                f"Failed operation: {operation}",
                extra={
                    "performance_metrics": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "status": "failed",
                        "error": str(e)
                    },
                    "context": context
                },
                exc_info=True
            )
            raise
    
    def log_metrics(self, metrics: Dict[str, Any], operation: Optional[str] = None):
        """Log performance metrics."""
        self.logger.info(
            f"Performance metrics{f' for {operation}' if operation else ''}",
            extra={
                "performance_metrics": {
                    "operation": operation,
                    "metrics": metrics,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        )
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get statistics for all timed operations."""
        with self._lock:
            if not self._operation_times:
                return {}
            
            # Convert deque to list for processing
            operations = list(self._operation_times)
            durations = [op["duration"] for op in operations]
            successful_ops = [op for op in operations if op["status"] == "success"]
            failed_ops = [op for op in operations if op["status"] == "failed"]
            
            return {
                "total_operations": len(operations),
                "successful_operations": len(successful_ops),
                "failed_operations": len(failed_ops),
                "total_time": sum(durations),
                "average_time": sum(durations) / len(durations),
                "min_time": min(durations),
                "max_time": max(durations),
                "success_rate": len(successful_ops) / len(operations) if operations else 0,
                "recent_operations": operations[-10:] if len(operations) > 10 else operations
            }


class PipelineLogger:
    """Main logger class for the pipeline with enhanced functionality."""
    
    def __init__(self, name: str):
        self.name = name
        self._logger = logging.getLogger(name)
        self._performance_logger = PerformanceLogger(self._logger)
        self._correlation_id: Optional[str] = None
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking."""
        self._correlation_id = correlation_id
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log with additional context information."""
        extra = kwargs.get('extra', {})
        if self._correlation_id:
            extra['correlation_id'] = self._correlation_id
        
        # Merge any additional context
        if 'context' in kwargs:
            extra['context'] = kwargs.pop('context')  # Remove from kwargs and add to extra
        
        kwargs['extra'] = extra
        self._logger.log(level, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    @property
    def performance(self) -> PerformanceLogger:
        """Access to performance logging functionality."""
        return self._performance_logger
    
    @contextmanager
    def operation_context(self, operation: str, **context):
        """Context manager for operation logging with automatic error handling."""
        error_context = ErrorContext(
            operation=operation,
            component=self.name,
            user_data=context,
            correlation_id=self._correlation_id
        )
        
        try:
            with self.performance.time_operation(operation, **context):
                yield error_context
        except Exception as e:
            get_error_handler().handle_error(e, error_context)
            raise


def get_logger(name: str) -> PipelineLogger:
    """Get a pipeline logger instance."""
    return PipelineLogger(name)


def setup_logging(force_reconfigure: bool = False) -> None:
    """Set up optimized logging configuration based on settings."""
    if not force_reconfigure and logging.getLogger().handlers:
        # Logging already configured
        return
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if hasattr(handler, 'close'):
            handler.close()
        root_logger.removeHandler(handler)
    
    # Get base logging configuration from settings
    log_config = settings.get_log_config()
    
    # Add structured formatter for production environments
    if settings.is_production() or settings.environment.value == "staging":
        log_config["formatters"]["structured"] = {
            "()": StructuredFormatter,
        }
    
    # Apply optimizations based on configuration
    if settings.logging_optimization_config.async_logging and not settings.is_development():
        # Setup async logging for better performance
        _setup_async_logging(log_config)
    
    # Add memory-efficient buffering for high-volume logging
    if settings.logging_optimization_config.log_buffer_size > 1024:
        _setup_buffered_logging(log_config)
    
    # Apply the configuration
    logging.config.dictConfig(log_config)
    
    # Set up log sampling for production
    if settings.is_production() and settings.logging_optimization_config.log_sampling_rate < 1.0:
        _setup_log_sampling()
    
    # Log the configuration setup (but only once)
    logger = get_logger("meshic_pipeline.logging")
    logger.info(
        "Optimized logging configured",
        context={
            "environment": settings.environment.value,
            "log_level": settings.log_level.value,
            "log_file": settings.log_file,
            "async_logging": settings.logging_optimization_config.async_logging,
            "log_sampling_rate": settings.logging_optimization_config.log_sampling_rate,
            "structured_logging": settings.is_production() or settings.environment.value == "staging"
        }
    )


def _setup_async_logging(log_config: Dict[str, Any]) -> None:
    """Setup asynchronous logging handlers."""
    # Wrap console handler with async handler
    if "console" in log_config["handlers"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.log_level.value)
        console_handler.setFormatter(logging.Formatter(settings.log_format))
        
        async_console = AsyncLogHandler(
            console_handler, 
            max_queue_size=settings.logging_optimization_config.max_log_queue_size
        )
        
        log_config["handlers"]["console"] = {
            "()": lambda: async_console,
            "level": settings.log_level.value,
        }
    
    # Wrap file handler with async handler if file logging is enabled
    if settings.log_file and "file" in log_config["handlers"]:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.log_file,
            maxBytes=settings.log_max_file_size,
            backupCount=settings.log_backup_count,
            encoding="utf-8"
        )
        file_handler.setLevel(settings.log_level.value)
        file_handler.setFormatter(logging.Formatter(settings.log_format))
        
        async_file = AsyncLogHandler(
            file_handler,
            max_queue_size=settings.logging_optimization_config.max_log_queue_size
        )
        
        log_config["handlers"]["file"] = {
            "()": lambda: async_file,
            "level": settings.log_level.value,
        }


def _setup_buffered_logging(log_config: Dict[str, Any]) -> None:
    """Setup buffered logging for better performance."""
    buffer_capacity = settings.logging_optimization_config.log_buffer_size // 100  # Rough estimate
    
    # Add memory handler for console
    if "console" in log_config["handlers"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(settings.log_level.value)
        console_handler.setFormatter(logging.Formatter(settings.log_format))
        
        memory_handler = OptimizedMemoryHandler(buffer_capacity, console_handler)
        memory_handler.setLevel(settings.log_level.value)
        
        log_config["handlers"]["console"] = {
            "()": lambda: memory_handler,
            "level": settings.log_level.value,
        }


def _setup_log_sampling() -> None:
    """Setup log sampling to reduce log volume in production."""
    # This would typically be handled by the AsyncLogHandler
    # but we can also add a custom filter
    class SamplingFilter(logging.Filter):
        def __init__(self, sample_rate: float):
            super().__init__()
            self.sample_rate = sample_rate
        
        def filter(self, record: logging.LogRecord) -> bool:
            # Always allow ERROR and CRITICAL
            if record.levelno >= logging.ERROR:
                return True
            
            # Sample other levels
            return random.random() <= self.sample_rate
    
    # Apply sampling filter to all handlers
    sampling_filter = SamplingFilter(settings.logging_optimization_config.log_sampling_rate)
    root_logger = logging.getLogger()
    
    for handler in root_logger.handlers:
        handler.addFilter(sampling_filter)


def log_performance(operation: str):
    """Decorator for automatic performance logging."""
    def decorator(func: F) -> F:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            with logger.performance.time_operation(operation, function=func.__name__):
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            with logger.performance.time_operation(operation, function=func.__name__):
                return await func(*args, **kwargs)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_function_calls(include_args: bool = False, include_result: bool = False):
    """Decorator for logging function calls."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            log_data = {"function": func.__name__}
            if include_args:
                log_data["args"] = str(args)
                log_data["kwargs"] = str(kwargs)
            
            logger.debug(f"Calling function: {func.__name__}", context=log_data)
            
            try:
                result = func(*args, **kwargs)
                if include_result:
                    logger.debug(
                        f"Function {func.__name__} completed",
                        context={**log_data, "result_type": type(result).__name__}
                    )
                return result
            except Exception as e:
                logger.error(
                    f"Function {func.__name__} failed: {str(e)}",
                    context=log_data,
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


# Initialize logging on module import
setup_logging() 