"""
Standardized exception hierarchy and error handling for the Suhail Pipeline.

This module provides:
- Custom exception classes for different types of errors
- Error context management
- Standardized error logging
- Retry mechanisms
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from contextlib import asynccontextmanager, contextmanager
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class ErrorSeverity(Enum):
    """Error severity levels for standardized error classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better error classification and handling."""
    NETWORK = "network"
    DATABASE = "database"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    PROCESSING = "processing"
    EXTERNAL_API = "external_api"
    FILE_SYSTEM = "file_system"
    AUTHENTICATION = "authentication"


@dataclass
class ErrorContext:
    """Context information for errors to aid in debugging and monitoring."""
    operation: str
    component: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_data: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary for logging."""
        return {
            "operation": self.operation,
            "component": self.component,
            "timestamp": self.timestamp.isoformat(),
            "user_data": self.user_data,
            "system_info": self.system_info,
            "correlation_id": self.correlation_id,
        }


class PipelineException(Exception):
    """Base exception class for all pipeline-related errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None,
        recoverable: bool = True,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context
        self.cause = cause
        self.recoverable = recoverable
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for structured logging."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.to_dict() if self.context else None,
            "cause": str(self.cause) if self.cause else None,
            "traceback": traceback.format_exc() if self.cause else None,
        }


class NetworkException(PipelineException):
    """Exception for network-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            **kwargs
        )


class DatabaseException(PipelineException):
    """Exception for database-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.DATABASE,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            **kwargs
        )


class ValidationException(PipelineException):
    """Exception for data validation errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            **kwargs
        )


class ConfigurationException(PipelineException):
    """Exception for configuration-related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            severity=kwargs.get('severity', ErrorSeverity.HIGH),
            recoverable=False,
            **kwargs
        )


class ProcessingException(PipelineException):
    """Exception for data processing errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.PROCESSING,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            **kwargs
        )


class ExternalAPIException(PipelineException):
    """Exception for external API errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.EXTERNAL_API,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            **kwargs
        )


class FileSystemException(PipelineException):
    """Exception for file system errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            category=ErrorCategory.FILE_SYSTEM,
            severity=kwargs.get('severity', ErrorSeverity.MEDIUM),
            **kwargs
        )


@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retriable_exceptions: tuple = (NetworkException, ExternalAPIException)


class ErrorHandler:
    """Centralized error handling and logging."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, datetime] = {}

    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        log_level: Optional[int] = None,
    ) -> None:
        """Handle and log an error with proper context."""
        
        if isinstance(error, PipelineException):
            error_dict = error.to_dict()
            severity = error.severity
        else:
            # Convert standard exceptions to pipeline exceptions
            pipeline_error = PipelineException(
                message=str(error),
                category=ErrorCategory.PROCESSING,
                severity=ErrorSeverity.MEDIUM,
                context=context,
                cause=error,
            )
            error_dict = pipeline_error.to_dict()
            severity = pipeline_error.severity

        # Determine log level based on severity
        if log_level is None:
            log_level_map = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL,
            }
            log_level = log_level_map[severity]

        # Log the error
        self.logger.log(
            log_level,
            "Error occurred: %s",
            error_dict["message"],
            extra={"error_details": error_dict},
        )

        # Update error tracking
        error_key = f"{error_dict['type']}:{error_dict.get('operation', 'unknown')}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        self._last_errors[error_key] = datetime.utcnow()

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            "error_counts": self._error_counts.copy(),
            "last_errors": {k: v.isoformat() for k, v in self._last_errors.items()},
            "total_errors": sum(self._error_counts.values()),
        }


# Global error handler instance
_global_error_handler = ErrorHandler(logger)


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return _global_error_handler


@contextmanager
def error_context(operation: str, component: str, **kwargs):
    """Context manager for error handling with automatic context creation."""
    context = ErrorContext(
        operation=operation,
        component=component,
        user_data=kwargs.get('user_data', {}),
        system_info=kwargs.get('system_info', {}),
        correlation_id=kwargs.get('correlation_id'),
    )
    
    try:
        yield context
    except Exception as e:
        get_error_handler().handle_error(e, context)
        raise


@asynccontextmanager
async def async_error_context(operation: str, component: str, **kwargs):
    """Async context manager for error handling."""
    context = ErrorContext(
        operation=operation,
        component=component,
        user_data=kwargs.get('user_data', {}),
        system_info=kwargs.get('system_info', {}),
        correlation_id=kwargs.get('correlation_id'),
    )
    
    try:
        yield context
    except Exception as e:
        get_error_handler().handle_error(e, context)
        raise


def with_retry(config: Optional[RetryConfig] = None):
    """Decorator for adding retry logic to functions."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: F) -> F:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.retriable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        if config.jitter:
                            import random
                            delay *= (0.5 + random.random() * 0.5)
                        
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.2fs",
                            attempt + 1, config.max_attempts, func.__name__, str(e), delay
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            "All %d attempts failed for %s. Last error: %s",
                            config.max_attempts, func.__name__, str(e)
                        )
                except Exception as e:
                    # Non-retriable exception
                    raise e
            
            # If we get here, all retries failed
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                except config.retriable_exceptions as e:
                    last_exception = e
                    if attempt < config.max_attempts - 1:
                        delay = min(
                            config.base_delay * (config.exponential_base ** attempt),
                            config.max_delay
                        )
                        if config.jitter:
                            import random
                            delay *= (0.5 + random.random() * 0.5)
                        
                        logger.warning(
                            "Attempt %d/%d failed for %s: %s. Retrying in %.2fs",
                            attempt + 1, config.max_attempts, func.__name__, str(e), delay
                        )
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(
                            "All %d attempts failed for %s. Last error: %s",
                            config.max_attempts, func.__name__, str(e)
                        )
                except Exception as e:
                    # Non-retriable exception
                    raise e
            
            # If we get here, all retries failed
            raise last_exception
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_exceptions(*exception_types: Type[Exception], reraise: bool = True):
    """Decorator for handling specific exception types."""
    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exception_types as e:
                get_error_handler().handle_error(e)
                if reraise:
                    raise
                return None
        return wrapper
    return decorator 
