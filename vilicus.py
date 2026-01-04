#!/usr/bin/env python3
"""
Vilicus Umbrae - The Shadow Guardian
A smart system monitoring and maintenance tool
"""
import os
import sys
import json
import yaml
import argparse
import traceback
from datetime import datetime
from typing import Dict, Any

# Import modules
from modules import disk, memory, cpu, logs, cleanup
from modules import reporter
from utils.logger import get_logger

VERSION = "1.0.0"

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config: {e}")
        sys.exit(1)

def load_state(state_path: str = "state.json") -> Dict[str, Any]:
    """Load previous state from JSON file."""
    if not os.path.exists(state_path):
        return {
            "meta": {"version": VERSION, "created_at": datetime.now().isoformat()},
            "last_run": {"timestamp": None, "status": None, "duration_seconds": None},
            "disk": {},
            "cpu": {},
            "logs": {},
            "backups": {}
        }
    try:
        with open(state_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("⚠️  Warning: Could not parse state.json, starting fresh")
        return load_state("/nonexistent")  # Return empty state

def save_state(state: Dict[str, Any], state_path: str = "state.json"):
    """Save current state to JSON file."""
    try:
        with open(state_path, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️ Warning: Could not save state: {e}")

def run_observations(config: Dict[str, Any], prev_state: Dict[str, Any], logger) -> Dict[str, Any]:
    """Run all observations modules."""
    logger.info("Starting system observations...")

    observations = {}

    # Disk monitoring
    logger.debug("Collecting disk usage...")
    observations["memory"] = memory.collect(config, prev_state)

    # Memory monitoring
    logger.debug("Collecting memory usage...")
    observations["memory"] = memory.collect(config, prev_state)

    # CPU monitoring
    logger.debug("Collecting CPU load...")
    observations["cpu"] = cpu.collect(config, prev_state)

    # Log monitoring
    logger.debug("Scanning log files...")
    observations["logs"] = logs.collect(config, prev_state)

    logger.info("Observations complete")
    return observations

def main():
    """Main orchestrator."""
    parser = argparse.ArgumentParser(
        description="Vilicus Umbrae - System Guardian",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    vilicus.py                  # Run in dry-run mode (safe)
    vilicus.py --execute        # Execute cleanup actions
    vilicus.py --report-only    # Generate report without observations
    vilicus.py --config custom.yaml  # Use custom config
        """
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute cleanup actions (default is dry-run)"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report from last run without new Observations"
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to config file (default:config.yaml)"
    )
    parser.add_argument(
        "--state",
        default="state.json",
        help="Path to state file (default: state.json)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Vilicus Umbrae {VERSION}"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Initialize logger
    logger = get_logger(config)

    logger.info(f"🛡️ Vilicus Umbrae v{VERSION} starting...")

    # Load previous state
    prev_state = load_state(args.state)

    # Determine execution mode
    dry_run = not args.execute
    mode = config.get("steward", {}).get("mode", "dry_run")

    if mode == "dry-run" and args.execute:
        logger.warning("Config set to dry-run but --execute flag provided. Using dry-run mode.")
    else:
        logger.info("Running in EXECUTE mode (actions will be performed)")

    start_time = datetime.now()
    observations = {}
    cleanup_results = {}

    try:
        # Run observations (unless report-only)
        if not args.report_only:
            observations = run_observations(config, prev_state, logger)

            # Count alerts
            alert_counts = {"critical": 0, "warning": 0, "info": 0}
            for module_data in observations.values():
                if isinstance(module_data, dict) and "alerts" in module_data:
                    for alert in module_data["alerts"]:
                        level = alert.get("level", "info")
                        alert_counts[level] = alert_counts.get(level, 0) + 1

            logger.info(
                f"Found {alert_counts.get('critical', 0)} critical, "
                f"{alert_counts.get('warning', 0)} warnings, "
                f"{alert_counts.get('info', 0)} info alerts"
            )

            # Plan cleanup actions
            if config.get("cleanup", {}).get("enabled", False):
                logger.info("Planning cleanup actions...")
                actions = cleanup.plan_cleanup(config, observations)
                logger.info(f"Planned {len(actions)} cleanup action(s)")

                if actions:
                    cleanup_results = cleanup.execute(actions, config, dry_run=dry_run)

                    executed = len(cleanup_results.get("executed", []))
                    failed = len(cleanup_results.get("failed", []))
                    skipped = len(cleanup_results.get("skipped", []))

                    logger.info(
                        f"Cleanup: {executed} executed, {failed} failed, {skipped} skipped"
                    )

            # Update state
            new_state = prev_state.copy()
            new_state["last_run"] = {
                "timestamp": start_time.isoformat(),
                "status": "success",
                "duration_seconds": (datetime.now() - start_time).total_seconds()
            }
            new_state.update(observations)

            save_state(new_state, args.state)
        else:
            logger.info("Report-only mode: using previous observations")
            observations = prev_state

        # Generate reports
        reporting_config = config.get("reporting", {})

        # Terminal summary
        if reporting_config.get("terminal_summary", {}).get("enabled", True):
            summary = reporter.generate_terminal_summary(observations, cleanup_results)
            print(summary)

        # Save markdown report
        if reporting_config.get("save_reports", True):
            logger.info("Generating markdown report...")
            md_report = reporter.generate_markdown_report(observations, cleanup_results, config)
            report_path = reporter.save_report(md_report, config)
            logger.info(f"Report saved: {report_path}")

        # Success
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Vilicus completed successfully in {duration:.2f}s")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️ Interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        logger.debug(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())






