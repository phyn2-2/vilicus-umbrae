"""Disk usage monitoring module."""
import os
import shutil
from typing import Dict, Any, List
from utils.diff import calculate_change, format_bytes, format_percentage

def collect(config: Dict[str, Any], prev_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect disk usage information.

    Args:
        config: Configuration dict
        prev_state: Previous state from state.json
    Returns:
        Dict with disk usage data and alerts
    """
    disk_config = config.get("disk", {})
    monitor_paths = disk_config.get("monitor_paths", ["/"])
    thresholds = disk_config.get("usage_thresholds", {})
    warning_pct = thresholds.get("warning_percent", 75)
    critical_pct = thresholds.get("critical_percent", 85)

    result = {
        "filesystems": {},
        "alerts": [],
        "summary": {}
    }

    # Get disk usage for each monitored path
    for path in monitor_paths:
        if not os.path.exists(path):
            result["alerts"].append({
                "level": "warning",
                "message": f"Monitored path does not exist: {path}"
            })
            continue

        try:
            usage = shutil.disk_usage(path)
            used_percent = (usage.used / usage.total) * 100

            fs_data = {
                "path": path,
                "total_bytes": usage.total,
                "used_bytes": usage.used,
                "free_bytes": usage.free,
                "used_percent": round(used_percent, 2),
                "total_human": format_bytes(usage.total),
                "used_human": format_bytes(usage.used),
                "free_human": format_bytes(usage.free)
            }

            # Check thresholds
            if used_percent >= critical_pct:
                result["alerts"].append({
                    "level":"critical",
                    "message": f"Disk usage critical on {path}: {used_percent:.1f}% (thresholds: {critical_pct}%)"
                })
            elif used_percent >= warning_pct:
                result["alerts"].append({
                    "level": "warning",
                    "message": f"Disk usage warning on {path}: {used_percent:.1f}% (thresholds: {warning_pct}%)"
                })

            # Compare with Previous state
            prev_disk = prev_state.get("disk", {}).get("filesystems", {})
            if path in prev_disk:
                prev_used = prev_disk[path].get("used_bytes", 0)
                change = calculate_change(prev_used, usage.used)
                fs_data["change"] = change

                # Check for growth
                growth_config = disk_config.get("growth_detection", {})
                if growth_config.get("enabled", False):
                    min_growth_mb = growth_config.get("min_growth_mb", 500)
                    min_growth_bytes = min_growth_mb * 1024 * 1024

                    if change["absolute_change"] > min_growth_bytes:
                        result["alerts"].append({
                            "level": "info",
                            "message": f"Significant disk growth on {path}: {format_bytes(change['absolute_change'])} ({change['percent_change']:.1f}%)"
                        })

            result["filesystems"][path] = fs_data

        except Exception as e:
            result["alerts"].append({
                "level": "error",
                "message": f"Failed to check disk usage for {path}: {e}"
            })

    # Generate summary
    if result["filesystems"]:
        total_space = sum(fs["total_bytes"] for fs in result["filesystems"].values())
        total_used = sum(fs["used_bytes"] for fs in result["filesystems"].values())
        avg_usage = (total_used / total_space) * 100 if total_space > 0 else 0

        result["summary"] = {
            "total_space": format_bytes(total_space),
            "total_used": format_bytes(total_used),
            "avg_usage_percent": round(avg_usage, 2)
        }

    return result



