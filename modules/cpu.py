"""CPU load monitoring module."""
import os
from typing import Dict, Any
import subprocess

def collect(config: Dict[str, Any], prev_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect CPU load information.
    Args:
        config: Configuration dict
        prev_state: Previous state from state.json
    Returns:
       Dict with CPU load data and alerts
    """
    cpu_config = config.get("cpu", {})
    warning_mult = cpu_config.get("warning_multiplier", 1.5)
    critical_mult = cpu_config.get("critical_multiplier", 2.0)

    result = {
        "load_average": {},
        "cores": 0,
        "alerts": []
    }

    try:
        # Get CPU core count
        result["cores"] = os.cpu_count() or 1

        # Get load averages
        load_1, load_5, load_15 = os.getloadavg()

        result["load_average"] = {
            "1_min": round(load_1, 2),
            "5_min": round(load_5, 2),
            "15_min": round(load_15, 2),
            "per_core_1min": round(load_1 / result["cores"], 2),
            "per_core_5min": round(load_5 / result["cores"], 2),
            "per_core_15min": round(load_15 / result["cores"], 2)
        }

        # Check thresholds (based on per-core load)
        warning_threshold = warning_mult
        critical_threshold = critical_mult

        per_core_load = load_1 / result["cores"]

        if per_core_load >= critical_threshold:
            result["alerts"].append({
                "level": "critical",
                "message": f"CPU load critical: {per_core_load:.2f} per core (threshold: {critical_threshold})"
            })
        elif per_core_load >= warning_threshold:
            result["alerts"].append({
                "level": "warning",
                "message": f"CPU load warning: {per_core_load:.2f} per core (threshold: {warning_threshold})"
            })

        # Get top CPU consumers
        try:
            ps_result = subprocess.run(
                ['ps', 'aux', '--sort=-%cpu'],
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
                            "cpu_percent": parts[2],
                            "command": ''.join(parts[10:])[:50]
                        })
                result["top_consumers"] = top_procs
        except:
            pass  # Non-critical, skip if fails

    except Exception as e:
        result["alerts"].append({
            "level": "error",
            "message": f"Failed to collect CPU info: {e}"
        })

    return result





