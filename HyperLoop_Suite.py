# ===========================
# HyperLoop Suite
# Launcher Module
# Author: Rob Hickling
#
# Just the launcher for the program
# Added logging and log rotation
# ===========================

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from HyperLoop.config import MAX_LOG_FILES


def cleanup_old_logs(logs_dir: Path, max_files: int) -> None:
    """
    Remove old log files if exceeding the maximum limit.
    """

    # Skip when no log directory exists
    if not logs_dir.exists():
        return

    # Skip when no files exist
    if max_files <= 0:
        return

    # Get all log files sorted by modification time (newest first)
    log_files = sorted(
        logs_dir.glob("HyperLog_*.log"), key=lambda i: i.stat().st_mtime, reverse=True
    )

    # Remove excess files
    if len(log_files) > max_files:
        for old_log in log_files[max_files:]:
            try:
                old_log.unlink()
                print("Warning: Max log files reached")
                print(f"Removed: Old log file: {old_log.name}")
            except OSError as e:
                print(f"Warning: Could not remove old log file {old_log.name}: {e}")


# --------------------------------------------------------------------------------------------------
# Main execution

if __name__ == "__main__":
    # Create log directory if it doesn't exist
    log_dir = Path("HyperLoop/logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clean up old logs before creating new one
    print("Pre-processing...")
    print(f"{'-' * 20}", flush=True)
    cleanup_old_logs(log_dir, MAX_LOG_FILES)

    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"HyperLog_{timestamp}.log"

    # Build the command to run the HyperLoop suite
    cmd = [
        sys.executable,
        "-c",
        "from HyperLoop.scripts.HyperLoop import HyperLoop; suite = HyperLoop(); suite.run_loop()",
    ]

    # Execute with tee logging (secure version without shell=True)
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=str(Path.cwd()),
            text=True,
        )
    except (OSError, subprocess.SubprocessError) as e:
        print(f"Error starting HyperLoop process: {e}")
        sys.exit(1)

    # Use tee-like functionality by writing to both console and file
    with log_file.open("w") as f:
        for line in process.stdout:
            print(line, end="")  # Output to console
            f.write(line)  # Write to log file

    process.wait()
