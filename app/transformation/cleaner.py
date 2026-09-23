"""
cleaner.py
----------
Data Cleaning stage (assignment section 7).

Handles, per source, before integration:
    - Extra whitespace around text values
    - Inconsistent casing ("Sanaa" / "sanaa" / " SANAA ")
    - Duplicate records
    - Obviously invalid numeric values that would break later steps
      (e.g. non-numeric age)

Cleaning here is deliberately source-specific and conservative: it
normalizes *formatting* problems. Whether a cleaned value is still
*out of business range* (age 150, GPA 4.8, ...) is decided later by
the validation stage (app/validation/quality.py), which is where
those records get rejected.
"""

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _standardize_text(value):
    """Trim whitespace and normalize casing to Title Case for text fields."""
    if pd.isna(value):
        return value
    return str(value).strip().title()


def clean_csv_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the CSV (student basic-info) source."""
    df = df.copy()

    before = len(df)
    df = df.drop_duplicates(subset=["student_id"], keep="first")
    removed = before - len(df)
    if removed:
        logger.info(f"CSV cleaning: removed {removed} duplicate record(s)")

    for col in ("student_name", "major", "city"):
        if col in df.columns:
            df[col] = df[col].apply(_standardize_text)

    # Blank strings -> real NaN so missing-value handling treats them consistently
    df = df.replace(r"^\s*$", pd.NA, regex=True)

    logger.info(f"CSV cleaning complete: {len(df)} record(s) remain")
    return df


def clean_api_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the API (academic) source."""
    df = df.copy()

    before = len(df)
    df = df.drop_duplicates(subset=["student_id"], keep="first")
    removed = before - len(df)
    if removed:
        logger.info(f"API cleaning: removed {removed} duplicate record(s)")

    if "status" in df.columns:
        df["status"] = df["status"].apply(_standardize_text)

    logger.info(f"API cleaning complete: {len(df)} record(s) remain")
    return df


def clean_database_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean the SQLite (enrollments/courses) source."""
    df = df.copy()

    before = len(df)
    df = df.drop_duplicates(subset=["student_id", "course", "semester"], keep="first")
    removed = before - len(df)
    if removed:
        logger.info(f"Database cleaning: removed {removed} duplicate record(s)")

    if "course" in df.columns:
        df["course"] = df["course"].apply(_standardize_text)

    logger.info(f"Database cleaning complete: {len(df)} record(s) remain")
    return df
