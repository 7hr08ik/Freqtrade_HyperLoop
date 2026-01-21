# ===========================
# HyperLoop Suite
# Terminal Management Module
# Author: Rob Hickling
#
# Launch seperate windows for Hyperopt to run
# ===========================


import shutil


class TerminalManager:
    """
    Handle terminal window creation for Linux.
    """

    @staticmethod
    def create_window_command(cmd: list[str], cwd: str, log_file: str) -> list[str]:
        """
        Create Linux terminal window command that auto-closes when done.
        """

        # Build the base command with conda activation
        cmd_str = " ".join(cmd)

        # Use simple tee command to capture all output
        base_cmd = (
            f'cd "{cwd}" && conda activate freqtrade 2>/dev/null || true && '
            f"{cmd_str} 2>&1 | tee {log_file}"
        )

        # Add auto-close command
        full_cmd = (
            f'{base_cmd}; echo "Hyperopt completed, closing window in 3 seconds..."; sleep 3; exit'
        )

        # Try common Linux terminals in order of preference
        terminals = {
            "konsole": ["konsole", "-e", "bash", "-c", full_cmd],
            "gnome-terminal": ["gnome-terminal", "--", "bash", "-c", full_cmd],
            "xterm": ["xterm", "-e", "bash", "-c", full_cmd],
        }

        for term, window_cmd in terminals.items():
            # noinspection PyDeprecation
            if shutil.which(term):
                print(f"Starting hyperopt in new terminal: {term}", flush=True)
                return window_cmd

        # Fallback to current terminal
        print("No suitable terminal found, using current terminal", flush=True)
        return cmd
