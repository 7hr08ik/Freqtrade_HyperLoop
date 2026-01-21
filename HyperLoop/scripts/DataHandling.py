# ===========================
# HyperLoop Suite
# Data Handling Module
# Author: Rob Hickling
#
# Create results data
# ===========================

import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


class DataHandling:
    """
    Manage data and results.
    """

    def __init__(self):
        # -------------------------
        # Set paths
        # -------------------------
        hypersuite_root = Path(__file__).resolve().parent.parent
        self.results_file = hypersuite_root / "top_results.json"

        # -------------------------
        # Clean old data
        # -------------------------
        self.clean_data_file()
        self.clear_old_results()

        # -------------------------
        # Load existing data
        # -------------------------
        self.data = self.load_data()

    # ----------------------------------------------------------------------------------------------
    # Cleanup

    def clean_data_file(self) -> None:
        """
        Remove existing data file for clean start.
        """

        if self.results_file.exists():
            self.results_file.unlink()
            print("Removed: Existing top_results.json for clean start")

    @staticmethod
    def clear_old_results():
        """
        Ensure the results folder is empty at the start of the script.
        """

        hypersuite_root = Path(__file__).resolve().parent.parent
        runs_dir = hypersuite_root / "results"

        # Validate path to prevent directory traversal
        if not runs_dir.is_relative_to(hypersuite_root):
            raise RuntimeError(f"Invalid results directory path: {runs_dir}")

        if runs_dir.exists():
            # Count items before deletion
            items = list(runs_dir.iterdir())
            if items:
                try:
                    # Remove all contents with safety checks
                    for item in runs_dir.iterdir():
                        # Additional safety: ensure we're only deleting within the expected directory
                        if not item.is_relative_to(runs_dir):
                            print(f"Warning: Skipping unsafe path: {item}")
                            continue
                            
                        if item.is_file():
                            item.unlink()
                        elif item.is_dir():
                            shutil.rmtree(item)
                    print(f"Removed: {len(items)} item from Results folder")
                except OSError as e:
                    print(f"Warning: Could not clear results folder: {e}")
            else:
                print("Warning: Results folder is already empty")
        else:
            # Create the directory if it doesn't exist
            runs_dir.mkdir(parents=True, exist_ok=True)
            print("Created: Results folder")

    # ----------------------------------------------------------------------------------------------
    # Helpers

    def save_data(self):
        """
        Save current data to file.
        """

        try:
            with self.results_file.open("w") as f:
                json.dump(self.data, f, indent=2)
        except OSError as e:
            print(f"Warning: Could not save data: {e}")

    def load_data(self) -> dict[str, Any]:
        """Load existing data or create new."""
        if self.results_file.exists():
            try:
                return json.loads(self.results_file.read_text())
            except (OSError, json.JSONDecodeError):
                pass

        return {
            "top_results": [],
            "failed_runs": [],
        }

    def add_result(self, result: dict[str, Any], top_n: int) -> None:
        """
        Add a new result and update top N.
        """

        self.data["top_results"] = self.update_top_results(result, top_n)
        self.save_data()

    def update_top_results(self, new_result: dict[str, Any], top_n: int) -> list[dict[str, Any]]:
        """
        Update top N results with new result.
        """

        top_results = self.data["top_results"].copy()

        if len(top_results) < top_n:
            top_results.append(new_result)
        else:
            worst_result = max(top_results, key=lambda x: x.get("objective", float("inf")))
            if new_result.get("objective", float("inf")) < worst_result.get(
                    "objective", float("inf")
            ):
                top_results.remove(worst_result)
                top_results.append(new_result)

        # Sort by objective (ascending - lower is better in hyperopt)
        top_results.sort(key=lambda x: x.get("objective", float("inf")))
        return top_results

    def record_failure(self, run_id: int, error: Exception):
        """
        Record none results from hyperopt as Failure.
        """

        failure_data = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "error": str(error),
            "error_type": type(error).__name__,
        }
        self.data["failed_runs"].append(failure_data)
        self.save_data()

    def get_top_results(self) -> list[dict[str, Any]]:
        """
        Get current top results.
        """

        return self.data["top_results"]

    def extract_data(self, run_dir: Path) -> dict[str, Any]:
        """
        Extract hyperopt results from log file using streaming parser.
        """

        log_file = run_dir / "hyperopt.log"
        if not log_file.exists():
            raise RuntimeError(f"hyperopt.log not found in {run_dir}")

        # Read log content
        content = log_file.read_text()

        # Check if hyperopt completed but found no good results
        if "Best result:" not in content:
            raise RuntimeError(
                "Hyperopt completed but found no good results (no Best result section)"
            )

        # Parse content
        return self.parse_log_file(content, run_dir)

    # ----------------------------------------------------------------------------------------------
    # Main Methods

    def parse_log_file(self, content: str, run_dir: Path) -> dict[str, Any]:
        """
        Parse log content string for results.
        """

        lines = content.split("\n")

        # Find the Best result line and extract the data line (2 lines after)
        best_result_line = None
        for i, line in enumerate(lines):
            if "Best result:" in line:
                # Skip the empty line and get the data line
                if i + 2 < len(lines):
                    best_result_line = lines[i + 2]
                break

        if not best_result_line:
            raise RuntimeError("Could not find Best result data line")

        # Parse the metrics from the single data line
        metrics = self.parse_result_data(best_result_line)

        # Extract epoch number from best result line to find the corresponding max drawdown line
        epoch_match = re.search(r"(\d+)/\d+:", best_result_line)
        if epoch_match:
            epoch_num = epoch_match.group(1)

            # Search for the line containing this epoch number in the table
            found_line = None
            for line in lines:
                # Look for the pattern: │ Best │ 69/100 │ (or just the epoch number in table)
                if f"{epoch_num}/100" in line and "│" in line:
                    found_line = line
                    break

            if found_line:
                # Split by │ and get the 9th column (index 8) for max drawdown
                columns = found_line.split("│")
                if len(columns) > 9:
                    max_dd_column = columns[9].strip()
                    # Handle case where max drawdown is 0% and shows as --
                    if max_dd_column == "--":
                        max_dd_column = "0.000 USDT (0.00%)"
                    if max_dd_column:
                        metrics["max_drawdown"] = max_dd_column
        else:
            # Fallback: Search entire content for max drawdown patterns
            max_dd_match = re.search(
                r"Max drawdown\s*:\s*([\d.]+)\s+USDT\s*\(\s*([\d.]+)%\)", content
            )
            if max_dd_match:
                metrics["max_drawdown"] = f"{max_dd_match.group(1)} USDT ({max_dd_match.group(2)}%)"
            else:
                # Pattern 2: Just look for "Max drawdown" followed by numbers
                max_dd_match2 = re.search(r"Max drawdown\s*[:\s]+([\d.]+)", content)
                if max_dd_match2:
                    metrics["max_drawdown"] = max_dd_match2.group(1)

        # Parse parameters (look for all parameter sections)
        params = {}
        param_sections = {
            "buy_params": "# Buy parameters:",
            "sell_params": "# Sell parameters:",
            "protection_params": "# Protection parameters:",
            "roi_params": "# ROI parameters:",
            "stoploss_params": "# Stoploss parameters:",
            "trailing_params": "# Trailing stop parameters:",
            "max_open_trades": "# Max open trades parameters:",
        }

        for param_type, section_header in param_sections.items():
            in_section = False
            param_text = []

            for line in lines:
                if section_header in line:
                    # Special filter for ROI parameters - skip if loaded from strategy
                    if param_type == "roi_params" and "# value loaded from strategy" in line:
                        # print(f"Skipping '{param_type}' - loaded from strategy: {line}")
                        break
                    # print(f"Found '{param_type}' section at line: {line}")
                    # print(f"Section header matched: '{section_header}' in '{line}'")
                    in_section = True
                    continue

                if in_section:
                    if f"{param_type} = {{" in line:
                        # print(f"Found '{param_type}' start: {line}")
                        # Start collecting params - include this line's content after the brace
                        params_start = line.find("{") + 1
                        if params_start > 0:
                            param_text.append(line[params_start:])
                        continue
                    elif "}" in line:
                        # End of params - include content before the closing brace
                        params_end = line.find("}")
                        if params_end > 0:
                            param_text.append(line[:params_end])
                        # Join all collected text and parse
                        full_param_text = "".join(param_text)
                        if full_param_text.strip():
                            parsed_params = self.parse_parameters(full_param_text)
                            params[param_type] = parsed_params
                        break
                    elif "#" not in line:  # Only collect lines without #
                        param_text.append(line)

        return {
            "run": run_dir.name,
            "profit": metrics.get("total_profit", 0),
            "objective": metrics.get("objective"),
            "drawdown": metrics.get("max_drawdown"),
            "metrics": metrics,
            "params": params,
        }

    @staticmethod
    def parse_result_data(best_result_line: str) -> dict[str, Any]:
        """
        Parse metrics from a single best result line.
        """

        metrics = {}

        # Extract trades
        trades_match = re.search(r"(\d+)\s+trades", best_result_line)
        if trades_match:
            metrics["total_trades"] = int(trades_match.group(1))

        # Extract wins/draws/losses
        wdl_match = re.search(r"(\d+)/(\d+)/(\d+)\s+Wins/Draws/Losses", best_result_line)
        if wdl_match:
            wins, draws, losses = map(int, wdl_match.groups())
            metrics["wins_draws_losses"] = f"{wins}/{draws}/{losses}"
            total = wins + draws + losses
            metrics["win_rate"] = wins / total if total > 0 else 0

        # Extract average profit
        avg_profit_match = re.search(r"Avg profit\s+([\d.]+)%", best_result_line)
        if avg_profit_match:
            metrics["avg_profit"] = float(avg_profit_match.group(1))

        # Extract median profit
        median_profit_match = re.search(r"Median profit\s+([\d.]+)%", best_result_line)
        if median_profit_match:
            metrics["median_profit"] = float(median_profit_match.group(1))

        # Extract total profit (USDT amount)
        total_profit_match = re.search(r"Total profit\s+([\d.]+)\s+USDT", best_result_line)
        if total_profit_match:
            metrics["total_profit"] = float(total_profit_match.group(1))

        # Extract profit percentage
        profit_percent_match = re.search(
            r"Total profit\s+[\d.]+\s+USDT\s+\(\s*([\d.]+)%\)", best_result_line
        )
        if profit_percent_match:
            metrics["profit_percent"] = float(profit_percent_match.group(1))

        # Extract average duration
        avg_duration_match = re.search(r"Avg duration\s+([\d:]+)\s+min", best_result_line)
        if avg_duration_match:
            metrics["avg_duration"] = avg_duration_match.group(1)

        # Extract objective
        objective_match = re.search(r"Objective:\s+([-\d.]+)", best_result_line)
        if objective_match:
            metrics["objective"] = float(objective_match.group(1))

        return metrics

    @staticmethod
    def parse_parameters(params_text: str) -> dict[str, Any]:
        """
        Parse parameters from text.
        """

        # Handle JSON format parameters
        try:
            # Clean up JSON text - join all lines and clean
            cleaned_text = params_text.strip()

            # For ROI parameters, handle multi-line JSON specially
            if "minimal_roi" in cleaned_text:
                # Extract the JSON part more carefully for ROI
                lines = cleaned_text.split("\n")
                json_lines = []
                in_json = False

                for line in lines:
                    line = line.strip()
                    if "{" in line:
                        in_json = True
                        json_lines.append(line)
                    elif in_json:
                        json_lines.append(line)
                        if "}" in line:
                            break

                cleaned_text = "\n".join(json_lines)
            else:
                # For other parameters, remove whitespace between parameters
                cleaned_text = re.sub(r"\s+", " ", cleaned_text)
                # Remove trailing commas before closing braces
                cleaned_text = re.sub(r",(\s*})", r"\1", cleaned_text)
                # Remove trailing comma at the very end if it exists
                cleaned_text = re.sub(r",\s*$", "", cleaned_text)
                # Ensure proper JSON structure
                if not cleaned_text.startswith("{"):
                    cleaned_text = "{" + cleaned_text
                if not cleaned_text.endswith("}"):
                    cleaned_text = cleaned_text + "}"

            # Try to parse as JSON
            params = json.loads(cleaned_text)
            return params

        except (json.JSONDecodeError, Exception) as e:
            print(f"JSON parsing failed: {e}")
            print(f"Original text: {params_text[:200]}...")
            # Fallback to line-by-line parsing
            params = {}
            for line in params_text.split("\n"):
                line = line.strip()
                if not line or "#" in line or ":" not in line:
                    continue

                key, value = line.split(":", 1)
                key = key.strip().strip('"')
                value = value.strip().strip('"').rstrip(",")

                # Type conversion
                try:
                    params[key] = int(value) if "." not in value else float(value)
                except ValueError:
                    params[key] = value

        return params
