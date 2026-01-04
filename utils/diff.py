"""Utilities for comparing current and previous states."""

from typing import Any, Dict, Optional

def calculate_change(old_value: float, new_value: float) -> Dict[str, Any]:
    """
    Calculate change between two values.

    Args:
        old_value: Previous value
        new_value: Current value
    Returns:
        Dict with absolute_change, percent_change and trend
    """
    if old_value == 0:
        return {
            "absolute_change": new_value,
            "percent_change": 100.0 if new_value > 0 else 0.0,
            "trend": "new"
        }

    absolute_change = new_value - old_value
    percent_change = (absolute_change / old_value) * 100

    if absolute_change > 0:
        trend = "increasing"
    elif absolute_change < 0:
        trend = "decreasing"
    else:
        trend = "stable"

    return {
        "absolute_change": round(absolute_change, 2),
        "percent_change": round(percent_change, 2),
        "trend": trend
    }

def format_bytes(bytes_value: int) -> str:
    """
    Format bytes into human-readable string.
    Args:
        bytes_value: Size in bytes
    Returns:
        Formatted string (e.g., "1.5 GB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"

def format_percentage(value: float, total: float) -> str:
    """
    Format value as percentage of total.

    Args:
        value: Current value
        total: Total value
    """
    if total == 0:
        return "0%"
    percent = (value / total) * 100
    return f"{percent:.1f}%"

def detect_anomaly(
    current_value: float,
    history: list,
    threshold_percent: float = 20.0
) -> Optional[str]:
    """
    Detect if current value is anomalous compared to history.
    Args:
        current_value: Current measurement
        history: List of previous values
        threshold_percent: Threshold for anomaly detection
    Returns:
        Anomaly description or None
    """
    if not history or len(history) < 2:
        return None

    avg = sum(history) / len(history)
    if avg == 0:
        return None

    deviation_percent = abs(((current_value - avg) / avg) * 100)

    if deviation_percent > threshold_percent:
        direction = "higher" if current_value > avg else "lower"
        return f"{deviation_percent:.1f}% {direction} than average"

    return None

def get_trend_indicator(percent_change: float) -> str:
    """
    Get visual trend indicator.

    Args:
        percent_change: Percentage change
    Returns:
        Emoji indicator
    """
    if percent_change > 5:
        return "📈"
    elif percent_change < -5:
        return "📉"
    else:
        return "➡️"









