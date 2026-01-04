"""Report generation module."""
import os
from datetime import datetime
from typing import Dict, Any

def generate_terminal_summary(observations: Dict[str, Any], cleanup_results: Dict[str, Any]) -> str:
    """
    Generate brief terminal summary.
    Args:
        observations: All observations
        cleanup_results: Cleanup execution results

    Returns:
        Formatted string for terminal output
    """
    lines = []
    lines.append("\n" + "="*60)
    lines.append("🛡️ VILICUS UMBRAE - System Report")
    lines.append("="*60 + "\n")

    # Collect all alerts
    all_alerts = []
    for module_name, data in observations.items():
        if isinstance(data, dict) and "alerts" in data:
            for alert in data["alerts"]:
                all_alerts.append({
                    "module": module_name,
                    **alert
                })

    # Show alerts by severity
    critical = [a for a in all_alerts if a.get("level") == "critical"]
    warnings = [a for a in all_alerts if a.get("level") == "warning"]

    if critical:
        lines.append("🔴 CRITICAL ISSUES:")
        for alert in critical:
            lines.append(f" [{alert['module']}] {alert['message']}")
        lines.append("")

    if warnings:
        lines.append("⚠️ WARNINGS:")
        for alert in warnings:
            lines.append(f" [{alert['module']}] {alert['message']}")
        lines.append("")

    if not critical and not warnings:
        lines.append("✅  No critical issues or warnings detected\n")

    # Quick stats
    lines.append("📊 QUICK STATS:")

    if "disk" in observations and observations["disk"].get("summary"):
        summary = observations["disk"]["summary"]
        lines.append(f" Disk: {summary.get('avg_usage_percent', 0):.1f}% average usage")

    if "memory" in observations and observations["memory"].get("ram"):
        ram = observations["memory"]["ram"]
        lines.append(f"  RAM: {ram.get('used_percent', 0):.1f}% used ({ram.get('used_human', 'N/A')})")

    if "cpu" in observations and observations["cpu"].get("load_average"):
        load = observations['cpu']['load_average']
        lines.append(f" CPU: {load.get('1_min', 0):.2f} load average (1min)")

    lines.append("")

    # Cleanup summary
    if cleanup_results and not cleanup_results.get("dry_run"):
        executed = len(cleanup_results.get("executed", []))
        failed = len(cleanup_results.get("failed", []))

        if executed > 0:
            lines.append(f"🗑️   CLEANUP: {executed} action(s) executed")
        if failed > 0:
            lines.append(f"❌ CLEANUP: {failed} action(s) failed")
        lines.append("")

    lines.append("="*60 + "\n")

    return "\n".join(lines)

def generate_markdown_report(
    observations: Dict[str, Any],
    cleanup_results: Dict[str, Any],
    config: Dict[str, Any]
) -> str:
    """
    Generate detailed markdown report.
    Args:
        observations: All observations
        cleanup_results: Cleanup execution results
        config: Configuration dict
    Returns:
        Markdown formatted report
    """
    lines = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append(f"# Vilicus Umbrae System Report")
    lines.append(f"**Generated:** {timestamp}\n")
    lines.append("---\n")

    # Executive summary
    lines.append("## 🎯  Executive Summary\n")

    all_alerts = []
    for module_name, data in observations.items():
        if isinstance(data, dict) and "alerts" in data:
            all_alerts.extend(data["alerts"])

    critical_count = sum(1 for a in all_alerts if a.get("level") == "critical")
    warning_count = sum(1 for a in all_alerts if a.get("level") == "warning")

    if critical_count == 0 and warning_count == 0:
        lines.append("✅ **System Status:** HEALTHY")
    elif critical_count > 0:
        lines.append(f"🔴 **System Status:** CRITICAL ({critical_count} critical issue(s))")
    else:
        lines.append(f"⚠️ **System Status:** WARNING ({warning_count} warning(s)) ")

    lines.append("")

    # Disk Section
    if "disk" in observations:
        lines.append("## 💾 Disk Usage\n")
        disk = observations["disk"]

        for path, fs_data in disk.get("filesystems", {}).items():
            lines.append(f"### {path}")
            lines.append(f"- **Total:** {fs_data.get('total_human', 'N/A')}")
            lines.append(f"- **Used:** {fs_data.get('used_human', 'N/A')} ({fs_data.get('used_percent', 0):.1f}%)")
            lines.append(f"- **Free:** {fs_data.get('free_human', 'N/A')}")

            if "change" in fs_data:
                change = fs_data["change"]
                lines.append(f"- **Change:** {change.get('trend', 'unknown')} ({change.get('percent_change', 0):.1f}%)")

            lines.append("")

    # Memory Section
    if "memory" in observations:
        lines.append("##  🧠 Memory Usage\n")
        mem = observations["memory"]

        if "ram" in mem:
            ram = mem["ram"]
            lines.append("### RAM")
            lines.append(f"- **Total:** {ram.get('total_human', 'N/A')}")
            lines.append(f"- **Used:** {ram.get('used_human', 'N/A')} ({ram.get('used_percent', 0):.1f}%)")
            lines.append(f"- **Available:** {ram.get('available_human', 'N/A')}\n")

        if "swap" in mem and mem["swap"]:
            swap = mem["swap"]
            lines.append("### Swap")
            lines.append(f"- **Total:** {swap.get('total_human', 'N/A')}")
            lines.append(f"- **Used:** {swap.get('used_human', 'N/A')} ({swap.get('used_percent', 0):.1f}%)\n")

        if "top_consumers" in mem:
            lines.append("### Top Memory Consumers")
            for proc in mem["top_consumers"][:3]:
                lines.append(f"- '{proc.get('command', 'N/A')}' - {proc.get('mem_percent', 0)}%")
            lines.append("")

    # CPU Section
    if "cpu" in observations:
        lines.append("## ⚡ CPU Load\n")
        cpu = observations["cpu"]

        lines.append(f"**Cores:** {cpu.get('cores', 'N/A')}\n")

        if "load_average" in cpu:
            load = cpu["load_average"]
            lines.append("### Load Average")
            lines.append(f"- **1 min:** {load.get('1_min', 0):.2f}")
            lines.append(f"- **5 min:** {load.get('5_min', 0):.2f}")
            lines.append(f"- **15 min:** {load.get('15_min', 0):.2f}\n")

        if "top_consumers" in cpu:
            lines.append("### Top CPU Consumers")
            for proc in cpu["top_consumers"][:3]:
                lines.append(f"- '{proc.get('command', 'N/A')}' - {proc.get('cpu_percent', 0)}%")
            lines.append("")

    # Logs Section
    if "logs" in observations and observations["logs"].get("enabled") != False:
        lines.append("## 📝 Log Files\n")
        logs = observations["logs"]

        lines.append(f"**Total Size:** {logs.get('total_size_human', 'N/A')}\n")

        large_files = logs.get("large_files", [])
        if large_files:
            lines.append("### Large Log Files")
            for file_info in large_files[:5]:
                lines.append(f"- '{file_info.get('path', 'N/A')}' - {file_info.get('size_human', 'N/A')}")
            lines.append("")

    # Cleanup Section
    if cleanup_results:
        lines.append("## 🗑️ Cleanup Actions\n")

        if cleanup_results.get("dry_run"):
            lines.append("*Dry run mode - no actions were executed*\n")

        executed = cleanup_results.get("executed", [])
        if executed:
            lines.append("### Executed Actions")
            for result in executed:
                action = result.get("action", {})
                lines.append(f"- **{action.get('type', 'unknown')}:** {result.get('status', 'unknown')}")
            lines.append("")

        failed = cleanup_results.get("failed", [])
        if failed:
            lines.append("### Failed Actions")
            for result in failed:
                action = result.get("action", {})
                lines.append(f"- **{action.get('type', 'unknown')}:** {result.get('error', 'unknown error')}")
            lines.append("")

    lines.append("---")
    lines.append(f"*Report generated by Vilicus Umbrae at {timestamp}*")

    return "\n".join(lines)

def save_report(content: str, config: Dict[str, Any]) -> str:
    """
    Save report to file.

    Args:
        content: Report content
        config: Configuration dict

    Returns:
        Path to saved report
    """
    reporting_config = config.get("reporting", {})
    report_dir = reporting_config.get("report_dir", "./reports")

    os.makedirs(report_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"vilicus_report_{timestamp}.md"
    filepath = os.path.join(report_dir, filename)

    with open(filepath, 'w') as f:
        f.write(content)

    return filepath











