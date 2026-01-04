"""Safe shell command execution utility."""
import subprocess
import shlex
from typing import Tuple, Optional

class ShellError(Exception):
    """Raised when shell command fails."""
    pass

def run_command(
    command: str,
    check: bool = True,
    timeout: int = 30,
    dry_run: bool = False
) -> Tuple[int, str, str]:
    """
    Execute a shell command safely.
    Args:
        command: Command string to execute
        check: Raise exception on non-zero exit
        timeout: Command timeout in seconds
        dry_run: If True, only print what would be executed

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    if dry_run:
        return (0, f"[DRY-RUN] Would execute: {command}", "")

    try:
        # Use shlex to properly split command
        cmd_parts = shlex.split(command)

        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        if check and result.returncode != 0:
            raise ShellError(
                f"Command failed with exit code {result.returncode}: {command}\n"
                f"STDERR: {result.stderr}"
            )
        return (result.returncode, result.stdout, result.stderr)

    except subprocess.TimeoutExpired:
        raise ShellError(f"Command timed out after {timeout}s: {command}")
    except FileNotFoundError:
        raise ShellError(f"Command not found: {command.split()[0]}")
    except Exception as e:
        raise ShellError(f"Unexpected error running command: {e}")

def is_command_safe(command: str, forbidden_patterns: list) -> bool:
    """
    Check if command is safe to execute.
    Args:
        command: Command to check
        forbidden_patterns: List of dangerous patterns
    Returns:
        True if safe, False otherwise
    """
    command_lower = command.lower()
    for pattern in forbidden_patterns:
        if pattern.lower() in command_lower:
            return False
    return True

def get_command_output(command: str, default: str = "") -> str:
    """
    Get command output, return default on error.
    Args:
        command: Command to run
        default: Default value if command fails
    Returns:
        Command stdout or default value
    """
    try:
        code, stdout, stderr = run_command(command, check=False)
        return stdout.strip() if code == 0 else default
    except:
        return default



