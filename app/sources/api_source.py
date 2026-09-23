"""
api_source.py
-------------
Data Source 2: academic data (gpa, attendance, status) fetched over
HTTP from a REST API.

Flow implemented (per assignment section 5.2):
    HTTP Request -> Receive JSON -> Parse JSON -> Convert to structured data

Handles: connection errors, timeouts, HTTP error status codes,
invalid/malformed JSON, and empty responses.
"""

import time
from typing import Optional

import pandas as pd
import requests

from app.sources.mock_api_server import MockAPIServer
from app.utils.exceptions import SourceExtractionError
from app.utils.logger import get_logger

logger = get_logger(__name__)

_mock_server: Optional[MockAPIServer] = None


def _ensure_mock_server_running(port: int = 0) -> str:
    """Start the local mock API once and return its base URL."""
    global _mock_server
    if _mock_server is None:
        _mock_server = MockAPIServer(port=port).start()
        time.sleep(0.2)  # give the background thread a moment to bind
        logger.info(f"Mock academic API started at {_mock_server.base_url}")
    return _mock_server.base_url


def extract_api(
    base_url: Optional[str] = None,
    endpoint: str = "/api/academic",
    use_mock: bool = True,
    timeout_seconds: int = 5,
    max_retries: int = 3,
) -> pd.DataFrame:
    """
    Fetch academic records from a REST API and return them as a DataFrame.

    Raises:
        SourceExtractionError: on connection failure, timeout, bad HTTP
            status, invalid JSON, or an empty response, after retries
            are exhausted.
    """
    logger.info("API extraction started")

    if use_mock or not base_url:
        base_url = _ensure_mock_server_running()

    url = base_url.rstrip("/") + endpoint

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout_seconds)
            response.raise_for_status()

            if not response.content:
                raise SourceExtractionError("API returned an empty response")

            try:
                payload = response.json()
            except ValueError as exc:
                raise SourceExtractionError(f"API returned invalid JSON: {exc}") from exc

            if not payload:
                logger.warning("API extraction returned zero records")
                df = pd.DataFrame(columns=["student_id", "gpa", "attendance", "status"])
            else:
                df = pd.DataFrame(payload)
                logger.info(f"API records: {len(df)}")

            df["source"] = "API"
            return df

        except requests.exceptions.Timeout as exc:
            last_error = exc
            logger.warning(f"API request timed out (attempt {attempt}/{max_retries})")
        except requests.exceptions.ConnectionError as exc:
            last_error = exc
            logger.warning(f"API connection error (attempt {attempt}/{max_retries})")
        except requests.exceptions.HTTPError as exc:
            last_error = exc
            logger.warning(f"API returned HTTP error (attempt {attempt}/{max_retries}): {exc}")
        except SourceExtractionError as exc:
            last_error = exc
            logger.warning(f"API data error (attempt {attempt}/{max_retries}): {exc}")

        time.sleep(0.3 * attempt)  # simple backoff

    logger.error(f"API extraction failed after {max_retries} attempts: {last_error}")
    raise SourceExtractionError(f"API extraction failed after {max_retries} attempts: {last_error}")
