import sys
from types import SimpleNamespace
import pytest

# Provide a stub psutil module if not available
if 'psutil' not in sys.modules:
    sys.modules['psutil'] = SimpleNamespace(Process=lambda: SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=0)))

from src.meshic_pipeline import memory_utils
from src.meshic_pipeline.config import settings

MemoryStats = memory_utils.MemoryStats


def make_monitor(process_mb_sequence):
    seq = list(process_mb_sequence)

    def get_memory_stats():
        value = seq.pop(0) if seq else process_mb_sequence[-1]
        return MemoryStats(
            total_mb=0,
            available_mb=0,
            used_mb=0,
            percent_used=0,
            process_mb=value,
            gc_collections={0: 0, 1: 0, 2: 0},
            timestamp=None,
        )

    monitor = SimpleNamespace(
        get_memory_stats=get_memory_stats,
        force_gc=lambda: setattr(monitor, "gc_called", True),
        gc_called=False,
        should_trigger_gc=lambda: False,
    )
    return monitor


def test_optimize_batch_size_respects_memory(monkeypatch):
    monitor = make_monitor([195])
    monkeypatch.setattr(memory_utils, "get_memory_monitor", lambda: monitor)
    stub_settings = SimpleNamespace(
        memory_config=SimpleNamespace(max_memory_usage_mb=200),
        get_optimized_batch_size=lambda b, s: b,
    )
    monkeypatch.setattr(memory_utils, "settings", stub_settings)

    items = list(range(1000))
    batch = memory_utils.optimize_batch_size(items, 500, item_size_estimate_kb=100)
    assert batch == 51


def test_optimize_batch_size_uses_config_limit(monkeypatch):
    monitor = make_monitor([50])
    monkeypatch.setattr(memory_utils, "get_memory_monitor", lambda: monitor)
    stub_settings = SimpleNamespace(
        memory_config=SimpleNamespace(max_memory_usage_mb=200),
        get_optimized_batch_size=lambda b, s: 30,
    )
    monkeypatch.setattr(memory_utils, "settings", stub_settings)

    items = list(range(100))
    batch = memory_utils.optimize_batch_size(items, 500, item_size_estimate_kb=10)
    assert batch == 30


def test_memory_limit_triggers_gc(monkeypatch):
    monitor = make_monitor([10, 20])
    monkeypatch.setattr(memory_utils, "get_memory_monitor", lambda: monitor)
    stub_settings = SimpleNamespace(
        memory_config=SimpleNamespace(enable_memory_monitoring=True, max_memory_usage_mb=15),
        get_optimized_batch_size=lambda b, s: b,
    )
    monkeypatch.setattr(memory_utils, "settings", stub_settings)

    with memory_utils.memory_limit(15):
        pass

    assert monitor.gc_called is True
