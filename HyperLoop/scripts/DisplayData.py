# ===========================
# HyperLoop Suite
# Display Results Module
# Author: Rob Hickling
#
# Print formatted results to the terminal after loop completion
# ===========================

import json
from typing import Any


class DisplayData:
    """
    Display formatted results and loop progress.
    """

    # ----------------------------------------------------------------------------------------------
    # Functions

    @staticmethod
    def progress_bar(current: int, total: int):
        """
        Display progress bar for optimization runs.
        """

        percent = (current / total) * 100
        bar_length = 50
        filled = int(bar_length * current // total)
        bar = "█" * filled + "░" * (bar_length - filled)

        print(" -  Current Progress  -")
        print(f"\r[{bar}] {percent:.1f}% ({current}/{total})", end="", flush=True)

    @staticmethod
    def display_top_results(top_results: list[dict[str, Any]]) -> None:
        """
        Display current top results.
        """

        print(f"\nTOP {len(top_results)} HYPEROPT RESULTS")
        print(f"{'=' * 60}")

        for i, r in enumerate(top_results, start=1):
            print(f"#{i} — {r['run']}")
            print(f"  Objective   : {r.get('objective', 'N/A')}")
            print(f"  Total Trades: {r.get('metrics', {}).get('total_trades', 'N/A')}")
            print(f"  Total Profit: {r['profit']:.2f}")
            print(f"  Avg Profit  : {r.get('metrics', {}).get('avg_profit', 'N/A')}")
            print("\n  Parameters:")
            print(json.dumps(r["params"], indent=4))
            print("-" * 60)

        # Display results table
        DisplayData.display_results_table(top_results)

    @staticmethod
    def display_results_table(results: list[dict[str, Any]]) -> None:
        """
        Display all results in a formatted table for easy comparison.
        """

        if not results:
            return

        print(f"\n{' ' * 50}HYPEROPT RESULTS TABLE{' ' * 50}")

        # Define table headers
        headers = [
            "Run",
            "Trades",
            "Win/Draw/Loss - Win%",
            "Avg Profit",
            "Profit",
            "Avg Duration",
            "Objective",
            "Max Drawdown",
        ]

        # Calculate column widths
        col_widths = [len(header) for header in headers]

        # Prepare table data
        table_data = []
        for i, result in enumerate(results, start=1):
            metrics = result.get("metrics", {})

            # Extract run number from run name (e.g., "run_001_20231201_120000_123456" -> "1")
            run_name = result.get("run", f"Run {i}")
            if "_" in run_name:
                try:
                    run_num = int(run_name.split("_")[1])
                except (ValueError, IndexError):
                    run_num = i
            else:
                run_num = i

            # Extract trades
            trades = metrics.get("total_trades", "N/A")

            # Format win/draw/loss with separate alignment
            wdl = metrics.get("wins_draws_losses", "N/A")
            if wdl != "N/A" and "/" in wdl:
                win_rate = metrics.get("win_rate", 0) * 100
                # Split WDL components and format each with 4 character spacing
                wdl_parts = wdl.split("/")
                formatted_wdl = (
                    f"{int(wdl_parts[0]):>4}/{int(wdl_parts[1]):>4}/{int(wdl_parts[2]):>4}"
                )
                # Create formatted string with proper spacing for alignment
                wdl_formatted = f"{formatted_wdl:<15} {win_rate:>5.1f}%"
            else:
                wdl_formatted = wdl

            # Format profit
            total_profit = metrics.get("total_profit", 0)
            profit_percent = metrics.get("profit_percent", 0)
            if total_profit != 0:
                profit_str = f"{total_profit:>8.2f} USDT  ({profit_percent:>6.2f}%)"
            else:
                profit_str = "N/A"

            # Format other metrics
            avg_profit = metrics.get("avg_profit", 0)
            avg_profit_str = f"{avg_profit:>6.2f}%" if avg_profit != 0 else "N/A"

            avg_duration = metrics.get("avg_duration", "N/A")
            avg_duration_str = f"{avg_duration:>11}" if avg_duration != "N/A" else "N/A"

            objective = metrics.get("objective", "N/A")
            objective_str = f"{objective:>11.3f}" if objective != "N/A" else "N/A"

            # Extract max drawdown from the result structure
            max_drawdown = result.get("drawdown", "N/A")
            if max_drawdown and max_drawdown != "N/A":
                max_drawdown_str = f"{max_drawdown:>11}"
            else:
                max_drawdown_str = "N/A"

            # Add formatted data to table data
            row = [
                str(run_num),
                str(trades),
                wdl_formatted,
                avg_profit_str,
                profit_str,
                avg_duration_str,
                objective_str,
                max_drawdown_str,
            ]
            table_data.append(row)

            # Update column widths based on data
            for j, cell in enumerate(row):
                if len(str(cell)) > col_widths[j]:
                    col_widths[j] = len(str(cell))

        # Build results table
        # Top border
        top_border = "┏" + "┳".join("━" * (width + 2) for width in col_widths) + "┓"
        print(top_border)

        # Header row
        header_cells = []
        for i, header in enumerate(headers):
            header_cells.append(f" {header:^{col_widths[i]}} ")
        header_row = "┃" + "┃".join(header_cells) + "┃"
        print(header_row)

        # Separator
        separator = "┡" + "╇".join("━" * (width + 2) for width in col_widths) + "┩"
        print(separator)

        # Data rows
        for row in table_data:
            row_cells = []
            for i, cell in enumerate(row):
                # Right-align numeric columns, left-align text
                if i in [0, 1]:  # Run and Trades columns - centre align
                    cell_str = f" {str(cell):^{col_widths[i]}} "
                elif i in [2]:  # Win/Draw/Loss column - left align (already formatted internally)
                    cell_str = f" {str(cell):<{col_widths[i]}} "
                elif i in [
                    3,
                    4,
                    5,
                    6,
                    7,
                ]:  # Avg profit, Profit, Duration, Objective, Drawdown - right align
                    cell_str = f" {str(cell):>{col_widths[i]}} "
                else:  # Other columns - left align
                    cell_str = f" {str(cell):<{col_widths[i]}} "
                row_cells.append(cell_str)
            data_row = "┃" + "┃".join(row_cells) + "┃"
            print(data_row)

        # Bottom border
        bottom_border = "┗" + "┷".join("━" * (width + 2) for width in col_widths) + "┛"
        print(bottom_border)
