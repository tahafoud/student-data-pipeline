"""
csv_source.py
-------------
Data Source 1: the students' basic-info CSV file
(student_id, student_name, age, major, city).

All CSV-reading logic lives here, per the assignment requirement that
"CSV reading logic must not be placed directly inside main.py".
"""

from pathlib import Path

import pandas as pd

from app.utils.exceptions import SourceExtractionError
from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_csv(csv_path: str | Path) -> pd.DataFrame:
    """
    Read the students CSV file into a DataFrame.

    Raises:
        SourceExtractionError: if the file is missing, empty, or
            cannot be parsed as CSV.
    """
    csv_path = Path(csv_path)
    logger.info("CSV extraction started")

    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        raise SourceExtractionError(f"CSV file not found: {csv_path}")

    try:
        df = pd.read_csv(csv_path, dtype=str)  # read as str; typing happens in transform stage
    except pd.errors.EmptyDataError as exc:
        logger.error("CSV file is empty")
        raise SourceExtractionError("CSV file is empty") from exc
    except pd.errors.ParserError as exc:
        logger.error(f"CSV file could not be parsed: {exc}")
        raise SourceExtractionError(f"CSV file could not be parsed: {exc}") from exc

    if df.empty:
        logger.warning("CSV extraction returned zero records")
    else:
        logger.info(f"CSV records: {len(df)}")

    df["source"] = "CSV"
    return df
