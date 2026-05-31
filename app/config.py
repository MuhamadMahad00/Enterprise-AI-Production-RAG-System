"""
Configuration, logging, and utilities module.
Combines: settings, logger, latency tracker.
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

load_dotenv()


# ═══════════════════════════════════════════════════════════════
# SETTINGS
# ═══════════════════════════════════════════════════════════════

class Settings:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    VECTOR_DB_PATH = "data/vector_store"
    DOCUMENTS_PATH = "data/documents"

    TOP_K_RETRIEVAL = 5
    TOP_K_RERANK = 3
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    MAX_QUERY_LENGTH = 1000
    MIN_QUERY_LENGTH = 3
    GROUNDING_THRESHOLD = 0.30

    LLM_TEMPERATURE = 0.3
    LLM_MAX_TOKENS = 500

    BENCHMARK_PATH = "benchmark/questions.json"
    REPORTS_PATH = "reports"


settings = Settings()


# ═══════════════════════════════════════════════════════════════
# LOGGER
# ═══════════════════════════════════════════════════════════════

os.makedirs("reports", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("reports/app.log", mode="a", encoding="utf-8"),
    ]
)

logger = logging.getLogger("rag_system")


# ═══════════════════════════════════════════════════════════════
# LATENCY TRACKER
# ═══════════════════════════════════════════════════════════════

class LatencyTracker:
    def __init__(self):
        self.start_time = None
        self.stages = {}
        self._stage_start = None
        self._current_stage = None

    def start(self):
        self.start_time = time.time()
        self.stages = {}

    def start_stage(self, stage_name):
        self._current_stage = stage_name
        self._stage_start = time.time()

    def end_stage(self, stage_name=None):
        stage = stage_name or self._current_stage
        if stage and self._stage_start:
            self.stages[stage] = round(time.time() - self._stage_start, 4)
            self._stage_start = None
            self._current_stage = None

    def stop(self):
        return round(time.time() - self.start_time, 4)

    def get_breakdown(self):
        return dict(self.stages)
