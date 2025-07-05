"""
Memory management utilities for the Suhail Pipeline.

This module provides:
- Memory usage monitoring
- Automatic garbage collection
- Memory optimization strategies
- Resource cleanup utilities
"""

from __future__ import annotations

import gc
import psutil
import weakref
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Callable, Set
from contextlib import contextmanager
from functools import wraps
from dataclasses import dataclass
from datetime import datetime, timedelta

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_mb: float
    available_mb: float
    used_mb: float
    percent_used: float
    process_mb: float
    gc_collections: Dict[int, int]
    timestamp: datetime


class MemoryMonitor:
    """Monitor and manage memory usage."""
    
    def __init__(self):
        self._process = psutil.Process()
        self._last_gc_time = time.time()
        self._gc_threshold_seconds = 30.0  # Minimum time between forced GC
        self._memory_history: List[MemoryStats] = []
        self._max_history = 100
        self._weak_refs: Set[weakref.ref] = set()
        self._lock = threading.Lock()
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory usage statistics."""
        # System memory
        memory = psutil.virtual_memory()
        
        # Process memory
        process_memory = self._process.memory_info()
        
        # Garbage collection stats
        gc_stats = {i: gc.get_count()[i] for i in range(3)}
        
        stats = MemoryStats(
            total_mb=memory.total / (1024 * 1024),
            available_mb=memory.available / (1024 * 1024),
            used_mb=memory.used / (1024 * 1024),
            percent_used=memory.percent,
            process_mb=process_memory.rss / (1024 * 1024),
            gc_collections=gc_stats,
            timestamp=datetime.now()
        )
        
        # Store in history
        with self._lock:
            self._memory_history.append(stats)
            if len(self._memory_history) > self._max_history:
                self._memory_history.pop(0)
        
        return stats
    
    def should_trigger_gc(self) -> bool:
        """Check if garbage collection should be triggered."""
        if not settings.memory_config.enable_memory_monitoring:
            return False
        
        # Check time threshold
        current_time = time.time()
        if current_time - self._last_gc_time < self._gc_threshold_seconds:
            return False
        
        # Check memory threshold
        stats = self.get_memory_stats()
        return settings.should_trigger_gc(stats.process_mb)
    
    def force_gc(self) -> Dict[str, Any]:
        """Force garbage collection and return statistics."""
        start_time = time.time()
        start_stats = self.get_memory_stats()
        
        # Clean weak references
        self._clean_weak_refs()
        
        # Force garbage collection for all generations
        collected = []
        for generation in range(3):
            collected.append(gc.collect(generation))
        
        # Update last GC time
        self._last_gc_time = time.time()
        
        end_stats = self.get_memory_stats()
        duration = self._last_gc_time - start_time
        
        gc_result = {
            "duration_seconds": duration,
            "objects_collected": sum(collected),
            "collections_by_generation": collected,
            "memory_before_mb": start_stats.process_mb,
            "memory_after_mb": end_stats.process_mb,
            "memory_freed_mb": start_stats.process_mb - end_stats.process_mb,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(
            f"Garbage collection completed: freed {gc_result['memory_freed_mb']:.2f}MB in {duration:.3f}s",
            extra={"gc_stats": gc_result}
        )
        
        return gc_result
    
    def _clean_weak_refs(self):
        """Clean up dead weak references."""
        with self._lock:
            dead_refs = {ref for ref in self._weak_refs if ref() is None}
            self._weak_refs -= dead_refs
    
    def register_object(self, obj: Any, cleanup_callback: Optional[Callable] = None):
        """Register an object for memory monitoring."""
        def cleanup_wrapper(ref):
            self._weak_refs.discard(ref)
            if cleanup_callback:
                cleanup_callback()
        
        weak_ref = weakref.ref(obj, cleanup_wrapper)
        with self._lock:
            self._weak_refs.add(weak_ref)
    
    def get_memory_history(self, minutes: int = 10) -> List[MemoryStats]:
        """Get memory usage history for the last N minutes."""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        with self._lock:
            return [
                stats for stats in self._memory_history 
                if stats.timestamp >= cutoff_time
            ]
    
    def get_memory_trend(self) -> Dict[str, float]:
        """Get memory usage trend analysis."""
        with self._lock:
            if len(self._memory_history) < 2:
                return {"trend": 0.0, "avg_usage": 0.0, "peak_usage": 0.0}
            
            recent_stats = self._memory_history[-10:]  # Last 10 measurements
            
            memory_values = [stats.process_mb for stats in recent_stats]
            avg_usage = sum(memory_values) / len(memory_values)
            peak_usage = max(memory_values)
            
            # Calculate trend (simple linear regression slope)
            n = len(memory_values)
            x_values = list(range(n))
            x_mean = sum(x_values) / n
            y_mean = avg_usage
            
            numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, memory_values))
            denominator = sum((x - x_mean) ** 2 for x in x_values)
            
            trend = numerator / denominator if denominator != 0 else 0.0
            
            return {
                "trend": trend,  # MB per measurement
                "avg_usage": avg_usage,
                "peak_usage": peak_usage
            }


# Global memory monitor instance
_memory_monitor = MemoryMonitor()


def get_memory_monitor() -> MemoryMonitor:
    """Get the global memory monitor instance."""
    return _memory_monitor


@contextmanager
def memory_limit(max_memory_mb: Optional[float] = None):
    """Context manager that monitors memory usage and triggers cleanup if needed."""
    limit = max_memory_mb or settings.memory_config.max_memory_usage_mb
    monitor = get_memory_monitor()
    
    start_stats = monitor.get_memory_stats()
    
    try:
        yield monitor
        
        # Check memory usage at the end
        end_stats = monitor.get_memory_stats()
        if end_stats.process_mb > limit:
            logger.warning(
                f"Memory usage ({end_stats.process_mb:.2f}MB) exceeded limit ({limit}MB)",
                extra={"memory_stats": end_stats}
            )
            if settings.memory_config.enable_memory_monitoring:
                monitor.force_gc()
                
    except Exception as e:
        # Force cleanup on exception
        if settings.memory_config.enable_memory_monitoring:
            monitor.force_gc()
        raise
    
    finally:
        final_stats = monitor.get_memory_stats()
        memory_delta = final_stats.process_mb - start_stats.process_mb
        
        if abs(memory_delta) > 10:  # Log significant memory changes
            logger.debug(
                f"Memory usage changed by {memory_delta:+.2f}MB during operation",
                extra={
                    "start_memory": start_stats.process_mb,
                    "end_memory": final_stats.process_mb,
                    "delta": memory_delta
                }
            )


def memory_optimized(max_memory_mb: Optional[float] = None, auto_gc: bool = True):
    """Decorator for memory-optimized function execution."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_memory_monitor()
            
            # Check memory before execution
            if auto_gc and monitor.should_trigger_gc():
                monitor.force_gc()
            
            with memory_limit(max_memory_mb):
                return func(*args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            monitor = get_memory_monitor()
            
            # Check memory before execution
            if auto_gc and monitor.should_trigger_gc():
                monitor.force_gc()
            
            with memory_limit(max_memory_mb):
                return await func(*args, **kwargs)
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def optimize_batch_size(items: List[Any], base_batch_size: int, item_size_estimate_kb: float = 10.0) -> int:
    """Optimize batch size based on current memory usage and constraints."""
    monitor = get_memory_monitor()
    current_stats = monitor.get_memory_stats()
    
    # Calculate available memory
    available_memory_mb = settings.memory_config.max_memory_usage_mb - current_stats.process_mb
    available_memory_kb = max(available_memory_mb * 1024, 0)
    
    # Calculate optimal batch size
    max_items_by_memory = int(available_memory_kb / item_size_estimate_kb)
    max_items_by_config = settings.get_optimized_batch_size(base_batch_size, item_size_estimate_kb)
    
    # Use the most restrictive limit
    optimal_batch_size = min(
        base_batch_size,
        max_items_by_memory,
        max_items_by_config,
        len(items)  # Don't exceed available items
    )
    
    # Ensure minimum batch size
    optimal_batch_size = max(optimal_batch_size, 1)
    
    if optimal_batch_size != base_batch_size:
        logger.debug(
            f"Optimized batch size from {base_batch_size} to {optimal_batch_size} "
            f"(memory: {current_stats.process_mb:.1f}MB, available: {available_memory_mb:.1f}MB)"
        )
    
    return optimal_batch_size


def cleanup_resources(*objects):
    """Explicitly cleanup resources and trigger garbage collection if needed."""
    monitor = get_memory_monitor()
    
    # Clear references
    for obj in objects:
        if hasattr(obj, 'close'):
            try:
                obj.close()
            except Exception as e:
                logger.warning(f"Error closing resource: {e}")
        elif hasattr(obj, '__del__'):
            try:
                obj.__del__()
            except Exception as e:
                logger.warning(f"Error in destructor: {e}")
    
    # Clear from locals
    del objects
    
    # Force garbage collection if needed
    if monitor.should_trigger_gc():
        monitor.force_gc()


@contextmanager
def batch_processor(items: List[Any], batch_size: int, item_size_estimate_kb: float = 10.0):
    """Context manager for memory-optimized batch processing."""
    monitor = get_memory_monitor()
    
    # Optimize batch size based on current memory
    optimal_batch_size = optimize_batch_size(items, batch_size, item_size_estimate_kb)
    
    try:
        # Process in batches
        for i in range(0, len(items), optimal_batch_size):
            batch = items[i:i+optimal_batch_size]
            
            with memory_limit():
                yield batch
                
            # Periodic garbage collection between batches
            if i > 0 and i % (optimal_batch_size * 5) == 0:  # Every 5 batches
                if monitor.should_trigger_gc():
                    monitor.force_gc()
                    
    except Exception as e:
        logger.error(f"Error in batch processing: {e}")
        cleanup_resources()
        raise 
