"""Cleanup action execution module."""
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from utils.shell import run_command, is_command_safe

def plan_cleanup(config: Dict[str, Any], observations: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Plan cleanup actions based on observations.
    Args:
        config: Configuration dict
        observations: Combined observations from all modules
    Returns:
        List of planned actions
    """
    cleanup_config = config.get("cleanup", {})

    if not cleanup_config.get("enabled", False):
        return []

    actions = []

    # Package cache cleanup
    pkg_cache = cleanup_config.get("package_cache", {})
    if pkg_cache.get("enabled", False):
        # Check if disk usage is high
        disk_alerts = observations.get("disk", {}).get("alerts", [])
        high_disk_usage = any(
            alert["level"] in ["warning", "critical"]
            for alert in disk_alerts
        )

        if high_disk_usage:
            actions.append({
                "type": "package_cache_clean",
                "command": pkg_cache.get("command", "apt-get clean"),
                "requires_sudo": pkg_cache.get("requires_sudo", True),
                "reason": "High disk usage detected"
            })

    # Temp directory cleanup
    temp_dirs = cleanup_config.get("temp_dirs", {})
    if temp_dirs.get("enabled", False):
        min_age_days = temp_dirs.get("min_age_days", 7)
        paths = temp_dirs.get("paths", ["/tmp"])

        for temp_path in paths:
            if os.path.exists(temp_path):
                actions.append({
                    "type": "temp_cleanup",
                    "path": temp_path,
                    "min_age_days": min_age_days,
                    "reason": "Routine temp file cleanup"
                })

    return actions

def execute(actions: List[Dict[str, Any]], config:Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
    """
    Execute cleanup actions.
    Args:
        actions: List of actions to execute
        config: Configuration dict
        dry_run: If True, don't actually execute

    Returns:
        Dict with execution results
    """
    security_config = config.get("security", {})
    forbidden = security_config.get("forbid_actions", [])
    allowed_sudo = security_config.get("allow_sudo", [])

    results = {
        "executed": [],
        "failed": [],
        "skipped": [],
        "dry_run": dry_run
    }

    for action in actions:
        action_type = action.get("type")

        try:
            if action_type == "package_cache_clean":
                command = action.get("command")
                requires_sudo = action.get("requires_sudo", False)

                # Security check
                if not is_command_safe(command, forbidden):
                    results["skipped"].append({
                        "action": action,
                        "reason": "Command forbidden by security policy"
                    })
                    continue

                if requires_sudo and command not in allowed_sudo:
                    results["skipped"].append({
                        "action": action,
                        "reason": "Sudo command not in allowed list"
                    })
                    continue

                # Execute
                full_command = f"sudo {command}" if requires_sudo else command
                exit_code, stdout, stderr = run_command(
                    full_command,
                    check=False,
                    dry_run=dry_run
                )

                if exit_code == 0:
                    results["executed"].append({
                        "action": action,
                        "output": stdout,
                        "status": "success"
                    })
                else:
                    results["failed"].append({
                        "action": action,
                        "error": stderr,
                        "exit_code": exit_code
                    })

            elif action_type == "temp_cleanup":
                path = action.get("path")
                min_age_days = action.get("min_age_days", 7)

                if not os.path.exists(path):
                    results["skipped"].append({
                        "action": action,
                        "reason": f"Path does not exist: {path}"
                    })
                    continue

                # find and remove old files
                cutoff_time = time.time() - (min_age_days * 86400)
                removed_count = 0
                removed_size = 0

                if not dry_run:
                    for item in os.listdir(path):
                        item_path = os.path.join(path, item)
                        try:
                            if os.path.isfile(item_path):
                                mtime = os.path.getmtime(item_path)
                                if mtime < cutoff_time:
                                    size = os.path.getsize(item_path)
                                    os.remove(item_path)
                                    removed_count += 1
                                    removed_size += size
                        except (OSError, PermissionError):
                            continue

                results["executed"].append({
                    "action": action,
                    "removed_files": removed_count,
                    "freed_bytes": removed_size,
                    "status": "success" if not dry_run else "dry_run"
                })

        except Exception as e:
            results["failed"].append({
                "action": action,
                "error": str(e)
            })
    return results











