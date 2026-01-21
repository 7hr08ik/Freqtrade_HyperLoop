# ===========================
# HyperLoop Suite
# HyperLoop Module
# Author: Rob Hickling
#
# The main loop
# ===========================

import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Required for viewing current processes
import psutil

from HyperLoop.config import (
    CONFIG_NAME,
    EPOCHS,
    HYPEROPT_LOSS,
    NUM_RUNS,
    SPACES,
    STRAT_NAME,
    THREADS,
    TIMEFRAME_DETAIL,
    TIMERANGE,
    TOP_N,
)
from HyperLoop.scripts.DataHandling import DataHandling
from HyperLoop.scripts.DisplayData import DisplayData
from HyperLoop.scripts.TerminalManager import TerminalManager


# Constants for timing
CHECK_INTERVAL = 15  # Check every 15 seconds
MIN_WAIT_BEFORE_PROCESS_CHECK = 60  # Don't check processes for first minute


class HyperLoop:
    def __init__(self):
        # -------------------------
        # Pull settings from config
        # -------------------------
        self.strat_name = STRAT_NAME
        self.config_name = CONFIG_NAME
        self.hyperopt_loss = HYPEROPT_LOSS
        self.timerange = TIMERANGE
        self.timeframe_detail = TIMEFRAME_DETAIL
        self.spaces = SPACES
        self.epochs = EPOCHS
        self.threads = THREADS
        self.num_runs = NUM_RUNS
        self.top_n = TOP_N

        # -------------------------
        # Set paths
        # -------------------------
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.user_data_dir = self.project_root / "user_data"
        self.strategies_dir = self.user_data_dir / "strategies"
        self.hyperopt_results_dir = self.user_data_dir / "hyperopt_results"
        self.config_path = self.user_data_dir / self.config_name

        self.hypersuite_root = self.project_root / "HyperLoop"
        self.runs_dir = self.hypersuite_root / "results"

        # -------------------------
        # Initialize data file
        # -------------------------
        self.data = DataHandling()

        # -------------------------
        # Find freqtrade
        # -------------------------
        self.freqtrade_bin = self.find_freqtrade()
        print(f"\nFound! Freqtrade location: {self.freqtrade_bin}\n")

    # ----------------------------------------------------------------------------------------------
    # Utilities

    def clear_old_hyperopt_results(self, run_dir: Path) -> tuple[Path, None]:
        """
        Clean up files before starting a new run.
        """

        # Find current strategy JSON file
        strategy_json = self.strategies_dir / f"{self.strat_name}.json"

        # Remove existing strategy JSON file
        if strategy_json.exists():
            strategy_json.unlink()
            print(f"Removed existing strategy JSON: {strategy_json.name}")

        # Clean up run directory if it exists
        if run_dir.exists():
            run_dir_strategy_json = run_dir / f"{self.strat_name}.json"
            if run_dir_strategy_json.exists():
                run_dir_strategy_json.unlink()
                print(f"Removed strategy JSON from run directory: {run_dir_strategy_json.name}")

        return strategy_json, None

    def build_hyperopt_cmd(self) -> list[str]:
        """
        Build the hyperopt command.
        """

        return [
            self.freqtrade_bin,
            "hyperopt",
            "--config",
            str(self.config_path),
            "--hyperopt-loss",
            self.hyperopt_loss,
            "--strategy",
            self.strat_name,
            "--timerange",
            self.timerange,
            "--timeframe-detail",
            self.timeframe_detail,
            "--spaces",
            self.spaces,
            "--epochs",
            str(self.epochs),
            "-j",
            str(self.threads),
            "--print-all",
        ]

    @staticmethod
    def wait_for_hyperopt_completion(run_dir: Path, strategy_json: Path) -> Optional[Path]:
        """
        Wait for hyperopt completion by monitoring strategy JSON file.
        """

        print("Waiting for hyperopt to complete...\n", flush=True)

        # Variables
        check_interval = CHECK_INTERVAL
        min_wait_before_process_check = MIN_WAIT_BEFORE_PROCESS_CHECK
        start_time = time.time()

        # Check if JSON file exists with retry mechanism
        while True:
            max_retries = 3
            for attempt in range(max_retries):
                if strategy_json.exists():
                    # Double-check file exists and is readable
                    try:
                        with strategy_json.open("r") as f:
                            f.read(1)  # Test if file is readable
                        print(f"Hyperopt completed - {strategy_json.name} found\n")
                        print("Post-processing...")
                        time.sleep(2)  # Give it a moment to fully write files
                        return run_dir
                    except OSError:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        else:
                            raise RuntimeError(
                                f"Strategy JSON file found but not readable: {strategy_json}"
                            )
                time.sleep(0.5)

            # Check if any hyperopt processes are running
            hyperopt_running = False
            try:
                for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                    try:
                        cmdline = " ".join(proc.info["cmdline"] or [])
                        if "freqtrade" in cmdline and "hyperopt" in cmdline:
                            hyperopt_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
            except Exception as e:
                # If psutil fails, log the error and continue waiting
                print(f"psutil error while checking processes: {e}")

            # If no hyperopt processes are running and no JSON file, assume completion
            if (
                not hyperopt_running and (time.time() - start_time) > min_wait_before_process_check
            ):  # Give at least 60 seconds before checking
                print("Hyperopt process completed but no strategy JSON was generated")
                raise RuntimeError("Hyperopt completed but produced no strategy JSON file")

            # Show waiting progress
            time.sleep(check_interval)

    def handle_hyperopt_failure(self, run_id: int, run_dir: Path, error: Exception) -> None:
        """
        Handle failed hyperopt runs gracefully.
        """

        # Create file called FAILED if no results returned
        failure_file = run_dir / "FAILED"
        failure_data = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "error_type": type(error).__name__,
        }
        failure_file.write_text(json.dumps(failure_data, indent=2))

        # Record in data
        self.data.record_failure(run_id, error)

    # ----------------------------------------------------------------------------------------------
    # Functions

    @staticmethod
    def find_freqtrade() -> str:
        """
        Find the freqtrade executable.
        """

        # 1 - Same env as current python (conda / venv)
        candidate = Path(sys.executable).parent / "freqtrade"
        if candidate.exists():
            return str(candidate)

        # 2 - PATH (terminal)
        # noinspection PyDeprecation
        ft = shutil.which("freqtrade")
        if ft:
            return ft

        raise RuntimeError(
            "freqtrade executable not found.\nActivate your environment or install freqtrade."
        )

    def run_hyperopt_window(self, run_id: int, run_dir: Path) -> Optional[Path]:
        """
        Run hyperopt in a new terminal window.
        """

        strategy_json, _ = self.clear_old_hyperopt_results(run_dir)

        # Build the command for new terminal window
        cmd = self.build_hyperopt_cmd()

        # Define log file path for this run
        log_file = run_dir / "hyperopt.log"

        # Use TerminalManager for Linux window creation with log capture
        window_cmd = TerminalManager.create_window_command(
            cmd, str(self.project_root), str(log_file)
        )

        # Start hyperopt in new window
        subprocess.Popen(window_cmd, cwd=str(self.project_root))

        # Wait for hyperopt to complete by monitoring strategy JSON
        try:
            result = self.wait_for_hyperopt_completion(run_dir, strategy_json)
            return result
        except RuntimeError as e:
            print(f"Hyperopt completion error: {e}")
            # Handle the case where hyperopt completed but produced no results
            self.handle_hyperopt_failure(run_id, run_dir, e)
            return None

    def run_single(self, run_id: int) -> Optional[Path]:
        """
        Run a single hyperopt run.
        """

        # Variables
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        run_dir = self.runs_dir / f"run_{run_id:03d}_{timestamp}"
        run_dir.mkdir(parents=True, exist_ok=False)

        print(f"\nStarting hyperopt in {run_dir}", flush=True)

        # Attempt running hyperopt in new window
        try:
            return self.run_hyperopt_window(run_id, run_dir)
        except Exception as e:
            print(f"Run {run_id} failed: {e}")
            # Use better error recovery
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            run_dir = self.runs_dir / f"run_{run_id:03d}_{timestamp}"
            run_dir.mkdir(parents=True, exist_ok=True)
            self.handle_hyperopt_failure(run_id, run_dir, e)
            return None

    # ----------------------------------------------------------------------------------------------
    # Run full hyperopt suite

    def run_loop(self) -> None:
        print(f"{'=' * 60}", flush=True)
        print(f"Starting {self.num_runs} hyperopt runs...", flush=True)
        print(f"{'=' * 60}", flush=True)

        successful_runs = 0

        # The Loop
        for i in range(1, self.num_runs + 1):
            # Print progress bar
            DisplayData.progress_bar(i, self.num_runs)

            print(f"\n\n{'=' * 60}", flush=True)
            print(f"Starting run {i}/{self.num_runs}", flush=True)
            print(f"{'=' * 60}", flush=True)

            # Execute single hyperopt run
            run_dir = self.run_single(i)
            if not run_dir:
                print(f"Run {i} failed to start", flush=True)
                continue

            # Extract results from this run
            try:
                result = self.data.extract_data(run_dir)
                successful_runs += 1

                print(f"\nRun {i} completed successfully", flush=True)
                print(f"{'-' * 30}\n", flush=True)
                print(f"Objective   : {result['objective']:.2f}", flush=True)
                print(f"Total Trades: {result['metrics'].get('total_trades', 'N/A')}", flush=True)
                print(f"Profit      : {result['profit']:.2f}", flush=True)

                # Update top results using OptimizationState
                initial_count = len(self.data.get_top_results())
                self.data.add_result(result, self.top_n)
                new_count = len(self.data.get_top_results())

                # Add new top result to file
                if new_count > initial_count:
                    print(f"\nNew result added to top {new_count}", flush=True)
                else:
                    print(f"\nResult not in top {self.top_n}", flush=True)

                # Copy strategy JSON and log file for reference
                DataHandling.copy_hyperopt_results(self.strat_name, self.strategies_dir, run_dir)

            except RuntimeError as e:
                print(f"\nRun {i} produced no usable results: {e}", flush=True)
                (run_dir / "FAILED").write_text(str(e))

        # Clear progress line
        print(flush=True)

        # Get final top results from data
        top_results = self.data.get_top_results()

        # Final summary
        print(f"\n{'=' * 60}")
        print("OPTIMIZATION COMPLETE")
        print(f"Successful runs: {successful_runs}/{self.num_runs}")
        print(f"Final top results: {len(top_results)}")
        print(f"Results saved to: {self.data.results_file}")

        # Display final top results
        DisplayData.display_top_results(top_results)
