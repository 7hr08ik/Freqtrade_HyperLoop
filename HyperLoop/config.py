# ===========================
# HyperLoop Suite
# Configuration
# Author: Rob Hickling
# ===========================

# ---------------------------
# Run settings
# ---------------------------

# Number of hyperopt loops to complete
NUM_RUNS = 50

# Hyperopt epochs per run
EPOCHS = 400

# Hyperopt threads to utilize
THREADS = 14

# Number of results to save
TOP_N = 10

# Maximum number of HyperLoop log files to keep (0 = keep all)
MAX_LOG_FILES = 10

# ---------------------------
# Strategy settings
# ---------------------------

# Name of the strategy to test
STRAT_NAME = "strat-name"

# Name of the config file to use
CONFIG_NAME = "config.json"

# Loss function to use
HYPEROPT_LOSS = "SharpeHyperOptLoss"
# ShortTradeDurHyperOptLoss
# OnlyProfitHyperOptLoss
# SharpeHyperOptLoss
# SortinoHyperOptLoss
# MaxDrawDownHyperOptLoss
# CalmarHyperOptLoss
# ProfitDrawDownHyperOptLoss

# Space to optimize
SPACES = "buy"
# default, all, buy, sell, roi, stoploss, trailing, protection, trades.

# ---------------------------
# Time settings
# ---------------------------

# Format: "YYYYMMDD-YYYYMMDD"
# Example: "20240501-20241116"
TIMERANGE = "20240501-20241116"

# Intra-candle timeframe
TIMEFRAME_DETAIL = "1m"
