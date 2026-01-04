"""Memory usage monitoring module."""
from typing import Dict, Any
import subprocess
from utils.diff import format_bytes, format_percentage
import os

def collect(config: Dict[str, Any], prev_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect memory usage information.
    Args:
        config: Configuration dict
        prev_state: Previous state from state.json

    Returns:
        Dict with memory usage data and alerts
    """
    mem_config = config.get("memory", {})
    ram_warning = mem_config.get("ram_warning_percent", 80)
    ram_critical = mem_config.get("ram_critical_percent", 90)
    swap_config = mem_config.get("swap", {})
    monitor_swap = swap_config.get("monitor", True)
    swap_warning = swap_config.get("usage_warning_percent", 40)

    result = {
        "ram": {},
        "swap": {},
        "alerts": []
    }

    try:
        # Read /proc/meminfo for accurate data
        with open('/proc/meminfo', 'r') as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    value = int(parts[1]) * 1024  # Convert KB to bytes
                    meminfo[key] = value

        # Calculate RAM usage
        mem_total = meminfo.get('MemTotal', 0)
        mem_available = meminfo.get('MemAvailable', 0)
        mem_used = mem_total - mem_available
        mem_used_percent = (mem_used / mem_total) * 100 if mem_total > 0 else 0

        result["ram"] = {
            "total_bytes": mem_total,
            "used_bytes": mem_used,
            "available_bytes": mem_available,
            "used_percent": round(mem_used_percent, 2),
            "total_human": format_bytes(mem_total),
            "used_human": format_bytes(mem_used),
            "available_human": format_bytes(mem_available)
        }

        # Check RAM thresholds
        if mem_used_percent >= ram_critical:
            result["alerts"].append({
                "level": "critical",
                "message": f"RAM usage critical: {mem_used_percent:.1f}% (threshold: {ram_critical}%)"
            })
        elif mem_used_percent >= ram_warning:
            result["alerts"].append({
                "level": "warning",
                "message": f"RAM usage warning: {mem_used_percent:.1f}% (threshold: {ram_warning}%)"
            })

        # Handle swap if monitoring is enabled
        if monitor_swap:
            swap_total = meminfo.get('SwapTotal', 0)
            swap_free = meminfo.get('SwapFree', 0)
            swap_used = swap_total - swap_free
            swap_used_percent = (swap_used / swap_total) * 100 if swap_total > 0 else 0

            result["swap"] = {
                "total_bytes": swap_total,
                "used_bytes": swap_used,
                "free_bytes": swap_free,
                "used_percent": round(swap_used_percent, 2),
                "total_human": format_bytes(swap_total),
                "used_human": format_bytes(swap_used),
                "free_human": format_bytes(swap_free)
            }

            # Check swap thresholds
            if swap_total > 0 and swap_used_percent >= swap_warning:
                result["alerts"].append({
                    "level": "warning",
                    "message": f"Swap usage high: {swap_used_percent:.1f}% (threshold: {swap_warning})"
                })

        # Get top memory consumers
        try:
            ps_result = subprocess.run(
                ['ps', 'aux', '--sort=-%mem'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if ps_result.returncode == 0:
                lines = ps_result.stdout.strip().split('\n')
                top_procs = []
                for line in lines[1:6]:  # Top 5 processes
                    parts = line.split()
                    if len(parts) >= 11:
                        top_procs.append({
                            "user": parts[0],
                            "pid": parts[1],
                            "mem_percent": parts[3],
                            "command": ' '.join(parts[10:])[:50]
                        })
                result["top_consumers"] = top_procs
        except:
            pass  # Non-critical, skip if fails

    except Exception as e:
        result["alerts"].append({
            "level": "error",
            "message": f"Failed to collect memory info: {e}"
        })
    return result


