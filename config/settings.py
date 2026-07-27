"""Project-wide constants for the crypto-bot data layer."""

# Bitget USDT-M perpetual futures REST base URL.
BASE_URL = "https://api.bitget.com"
HISTORY_CANDLES_PATH = "/api/v2/mix/market/history-candles"

# Market scope.
PRODUCT_TYPE = "USDT-FUTURES"
GRANULARITY = "15m"
GRANULARITY_MS = 15 * 60 * 1000  # 900_000 ms per 15-minute bar.

# Symbols traded (Bitget symbol notation).
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# Intended historical range for the (future) backfill. UTC.
START_DATE = "2022-01-01T00:00:00Z"

# Request throttling.
MAX_REQUESTS_PER_SECOND = 5

# Directories.
RAW_PROBE_DIR = "data/raw/probe"
