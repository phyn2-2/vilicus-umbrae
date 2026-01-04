"""Backup monitoring module."""
import os
import glob
from datetime import datetime, timedelta
from typing import Dict, Any, List
from utils.diff import format_bytes, calculate_change

def collect(config: Dict[str, Any], prev_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Monitor backup directories and files
    Args:
        config: Configuration dict
        prev_state: Previous state from state.json

    Returns:
        Dict with backup status and alerts

    """
    backup_config = config.get("backups", {})

    if not backup_config.get("enabled", False):
        return {"enabled": False}

    expected_paths = backup_config.get("expected_paths", [])
    max_days = backup_config.get("max_days_since_last_backup", 3)
    size_change_warn = backup_config.get("size_change_warning_percent", 30)

    result = {
        "backup_locations": [],
        "alerts": [],
        "summary": {}
    }

    total_backup_size = 0
    total_backup_count = 0
    stale_backups = []

    for path_pattern in expected_paths:
        # Expand patterns like /home/*/backups
        matching_paths = glob.glob(os.path.expanduser(path_pattern))

        for backup_path in matching_paths:
            if not os.path.exists(backup_path):
                result["alerts"].append({
                    "level": "warning",
                    "message": f"Backup path does not exist: {backup_path}"
                })
                continue

            try:
                # Get all files in backup directory
                backup_files = []
                dir_size = 0
                latest_mtime = 0

                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        filepath = os.path.join(root, file)
                        try:
                            stat = os.stat(filepath)
                            file_size = stat.st_size
                            file_mtime = stat.st_mtime

                            backup_files.append({
                                "path": filepath,
                                "size": file_size,
                                "modified": file_mtime
                            })

                            dir_size += file_size
                            latest_mtime = max(latest_mtime, file_mtime)
                        except (OSError, PermissionError):
                            continue

                total_backup_size += dir_size
                total_backup_count += len(backup_files)

                # Check if backups are stale
                if latest_mtime > 0:
                    days_since_backup = (datetime.now().timestamp() - latest_mtime) / 86400

                    if days_since_backup > max_days:
                        stale_backups.append(backup_path)
                        result["alerts"].append({
                            "level": "warning",
                            "message": f"Stale backup detected: {backup_path} (last backup {days_since_backup:.1f} days ago)"
                        })

                # Store location info
                location_data = {
                    "path": backup_path,
                    "size_bytes": dir_size,
                    "size_human": format_bytes(dir_size),
                    "file_count": len(backup_files),
                    "latest_backup_age_days": (datetime.now().timestamp() - latest_mtime) / 86400 if latest_mtime > 0 else None
                }

                # Compare with previous state
                prev_backups = prev_state.get("backups", {}).get("backup_locations", [])
                prev_location = next(
                    (loc for loc in prev_backups if loc.get("path") == backup_path),
                    None
                )

                if prev_location:
                    prev_size = prev_location.get("size_bytes", 0)
                    change = calculate_change(prev_size, dir_size)
                    location_data["change"] = change

                    # Warn if size changed dramatically
                    if abs(change["percent_change"]) > size_change_warn:
                        result["alerts"].append({
                            "level": "info",
                            "message": f"Backup size changed significantly for {backup_path}: {change['percent_change']:.1f}%"
                        })

                result["backup_locations"].append(location_data)

            except Exception as e:
                result["alerts"].append({
                    "level": "error",
                    "message": f"Backup size changed significantly for {backup_path}: {change['percent_change']:.1f}%"
                })

    # Summary
    result["summary"] = {
        "total_locations": len(result["backup_locations"]),
        "total_size": format_bytes(total_backup_size),
        "total_file": total_backup_count,
        "stale_backups": len(stale_backups)

    }

    return result






