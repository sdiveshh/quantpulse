import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from security import chat_limiter, general_limiter  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_state(monkeypatch):
    monkeypatch.delenv("API_KEY", raising=False)
    chat_limiter.hits.clear()
    general_limiter.hits.clear()