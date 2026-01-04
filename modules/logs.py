"""Log file monitoring module."""
import os
from typing import Dict, Any, List
from utils.diff import format_bytes

def collect(config: Dict[str, Any], prev_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect log file information.
    Args:
        config: Configuration dict
        prev_state: Previous state from state.json
    Returns:
        Dict with log file data and alerts
    """
    logs_config = config.get("logs", {})

    if not logs_config.get("monitor", True):
        return {"enabled": False}

    log_paths = logs_config.get("paths", ["/var/log"])
    size_warning_mb = logs_config.get("size_warning_mb", 500)
    size_critical_mb = logs_config.get("size_critical_mb", 1024)

    result = {
        "directories": {},
        "large_files": [],
        "alerts": [],
        "total_size": 0
    }

    for log_dir in log_paths:
        if not os.path.exists(log_dir):
            continue

        try:
            dir_size = 0
            file_count = 0
            large_files = []

            for root, dirs, files in os.walk(log_dir):
                for file in files:
                    try:
                        filepath = os.path.join(root, file)
                        # Skip if not readable
                        if not os.access(filepath, os.R_OK):
                            continue

                        file_size = os.path.getsize(filepath)
                        dir_size += file_size
                        file_count += 1

                        file_size_mb = file_size / (1024 * 1024)

                        # Track large files
                        if file_size_mb >= size_warning_mb:
                            large_files.append({
                                "path": filepath,
                                "size_bytes": file_size,
                                "size_human": format_bytes(file_size),
                                "size_mb": round(file_size_mb, 2)
                            })
                    except (OSError, PermissionError):
                        continue  # Skip files we can't read

            result["directories"][log_dir] = {
                "total_size_bytes": dir_size,
                "total_size_human": format_bytes(dir_size),
                "file_count": file_count
            }

            result["total_size"] += dir_size

            # Check for critically large files
            for file_info in large_files:
                if file_info["size_mb"] >= size_critical_mb:
                    result["alerts"].append({
                        "level": "critical",
                        "message": f"Critical log file size: {file_info['path']} ({file_info['size_human']})"
                    })
                    result["large_files"].append(file_info)
                elif file_info["size_mb"] >= size_warning_mb:
                    result["alerts"].append({
                        "level": "warning",
                        "message": f"Large log file: {file_info['path']} ({file_info['size_human']})"
                    })
                    result["large_files"].append(file_info)

        except Exception as e:
            result["alerts"].append({
                "level": "error",
                "message": f"Failed to scan log directory {log_dir}: {e}"
            })

    # Add summary
    result["total_size_human"] = format_bytes(result["total_size"])

    return result





