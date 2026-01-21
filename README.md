# HyperLoop Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A hyperparameter optimization suite for Freqtrade that automates and enhances the strategy optimization
process through systematic multi-run hyperopt campaigns.

**Insired by:** https://github.com/mndrwd/freqtrade_hyperopt_loop

This tool was inspired by the above project. I decided I was a bit bored, and wanted to create a more robust,
fully automated system that I can use in a set and forget manner.

My understanding of hyperopt, is that it begins with randomized numbers, meaning every run will return completely
different results. This means I should run hyperopt multiple times and manually review those results in order to find
the best possible, correct numbers.

My current workflow is to optimize 1 trend at time, buy trends then sell trends etc. This process can obviously take a
very long time, and is very manual. My method for hyperopting my strategy may be wrong, it may be different to yours,
and its probably not the right way of doing things, but it is what it is. Using this tool I set up my strategy and
run this tool overnight, running XX loops of hyperopt. The result I wake up to is a table of the top XX results
(ordered by objective) that I can then manually filter through.

I built this project for my own current system and setup:

    OS: Manjaro Linux
    Terminal: Konsole
    
    Freqtrade Env: MiniConda Installation

## Features

- **Automated Multi-Run Optimization**: Execute multiple hyperopt runs sequentially with automatic result aggregation
- **Intelligent Result Management**: Automatically tracks and ranks the best performing strategy parameters
- **Cross-Platform Terminal Management**: Launches hyperopt runs in separate terminal windows for better resource
  management
- **Simple Logging**: Terminal execution logs with automatic log rotation
- **Configurable Parameters**: Fully customizable optimization settings through simple configuration files

## Prerequisites

- **Freqtrade (conda)**: A working Freqtrade installation
- **Python 3.8+**: Minimum required for the HyperLoop suite
- **Linux Environment**: Currently optimized for Linux systems
- **Trading Strategy**: At least one Freqtrade strategy to optimize
- **Configuration File**: A valid Freqtrade configuration file

## Installation

### 1. Download

```bash
Unpack into your main freqtrade directory
  Must be placed next to user_data folder
  NOT inside it

freqtrade/
  ├── user_data/
  ├── HyperLoop/             
  ├── HyperLoop_Suite.py     # Main launcher script
```

### 2. Install Dependencies

```bash
# Install required Python packages
pip install psutil
```

### 4. Configure HyperLoop

Edit the configuration file to your requirements:

```bash
# Open the config file
nano HyperLoop/config.py
```

Key configuration options:

- `STRAT_NAME`: Your strategy name
- `CONFIG_NAME`: Your Freqtrade config file
- `TIMERANGE`: Date range for optimization (format: "YYYYMMDD-YYYYMMDD")
- `NUM_RUNS`: Number of hyperopt runs to execute
- `EPOCHS`: Hyperopt epochs per run
- `THREADS`: Number of parallel threads to use

## Quick Start

### Basic Usage

1. **Configure Your Settings**
   ```python
   # In HyperLoop/config.py
   STRAT_NAME = "YourStrategyName"
   CONFIG_NAME = "your-config.json"
   TIMERANGE = "20240101-20241231"
   NUM_RUNS = 10
   EPOCHS = 100
   ```

2. **Run the Optimization Suite**
   ```bash
   python HyperLoop_Suite.py
   ```

3. **Monitor Progress**
    - Watch the real-time progress in your terminal
    - Check individual run logs in `HyperLoop/logs/`
    - View results in `HyperLoop/results/`

### Example Configuration

```python
# Strategy settings
STRAT_NAME = "UberStrat"
CONFIG_NAME = "config-hyp.json"
HYPEROPT_LOSS = "SharpeHyperOptLoss"

# Run settings
NUM_RUNS = 10
EPOCHS = 5
THREADS = 10
TOP_N = 10

# Data settings
TIMERANGE = "20240501-20241116"
TIMEFRAME_DETAIL = "1m"
SPACES = "buy"
```

## How It Works

### 1. **Initialization**

- HyperLoop detects your Freqtrade installation
- Sets up directory structure and logging
- Loads configuration parameters

### 2. **Multi-Run Execution**

- For each run in the configured range:
    - Creates a unique run directory with timestamp
    - Launches Freqtrade hyperopt in a new terminal window
    - Monitors progress and waits for completion
    - Captures results and handles errors gracefully

### 3. **Result Processing**

- Extracts performance metrics from each successful run
- Ranks results based objective score
- Maintains a top-N results list across all runs
- Saves strategy parameters and performance data

### 4. **Output Management**

- **Logs**: Detailed execution logs in `HyperLoop/logs/`
- **Results**: Individual run data in `HyperLoop/results/run_XXX_YYYYMMDD_HHMMSS/`
- **Top Results**: Consolidated best results in `HyperLoop/top_results.json`

## Project Structure

```
HyperLoop/
├── logs/                  # Execution logs
├── results/               # Individual run results
│   └── run_XXX_timestamp/
│       ├── hyperopt.log   # Run-specific log
│       └── Strategy.json  # Optimized parameters
├── scripts/               # Core modules
│   ├── HyperLoop.py       # Main optimization engine
│   ├── DataHandling.py    # Result processing
│   ├── DisplayData.py     # Progress display
│   └── TerminalManager.py # Terminal management
├── config.py              # Main configuration file
├── HyperLoop_Suite.py     # Main launcher script
└── top_results.json       # Consolidated best results
```

## Configuration Options

### Run Settings

- `NUM_RUNS`: Number of hyperopt loops to complete
- `EPOCHS`: Hyperopt epochs per run
- `THREADS`: Parallel threads to utilize
- `TOP_N`: Number of top results to save
- `MAX_LOG_FILES`: Maximum log files to keep (0 = unlimited)

### Strategy Settings

- `STRAT_NAME`: Name of the strategy to test
- `CONFIG_NAME`: Name of the config file to use
- `HYPEROPT_LOSS`: Loss function for optimization

### Data Settings

- `TIMERANGE`: Date range for backtesting (YYYYMMDD-YYYYMMDD)
- `TIMEFRAME_DETAIL`: Intra-candle timeframe
- `SPACES`: Parameter spaces to optimize (buy, sell, roi, stoploss, etc.)

## Troubleshooting

### Common Issues

1. **"freqtrade executable not found"**
    - Ensure your Freqtrade environment is activated
    - Verify freqtrade is in your PATH
    - Check that freqtrade is properly installed

2. **"No strategy JSON was generated"**
    - Check your strategy file for syntax errors
    - Verify the strategy name matches exactly
    - Review the hyperopt log for specific errors

3. **Permission errors**
    - Ensure write permissions in the HyperLoop directory
    - Check file permissions for your user_data directory

## License

This project is licensed under the MIT Licence - see the [LICENCE](LICENSE) file for details.

## Acknowledgments

- **Freqtrade Team**: For the excellent trading bot framework
- **Contributors**: Myself, with the assistance of Windsurf, and Pycharm

**Happy Trading!**
