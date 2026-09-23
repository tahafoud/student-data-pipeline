"""
transformer.py
--------------
Data Transformation stage (assignment section 8).

Implements, in order:
    8.1 Column name standardization (Student ID / studentID / Student_Name -> snake_case)
    8.2 Missing-value handling, with a documented strategy per field
    8.3 Data type conversion ("21" -> 21, "3.45" -> 3.45)
    8.4 Derived columns: performance_level (from GPA), attendance_status (from attendance)
"""

import re

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# 8.1 Column name standardization
# ---------------------------------------------------------------------------
def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to snake_case regardless of how a source
    named them, e.g.:
        "Student ID" / "studentID" / "Student_Name" -> "student_id" / "student_name"
    """
    df = df.copy()

    def normalize(col: str) -> str:
        col = re.sub(r"(?<!^)(?=[A-Z])", "_", col)   # camelCase -> camel_Case
        col = col.strip().lower()
        col = re.sub(r"[\s\-]+", "_", col)
        col = re.sub(r"_+", "_", col)
        col = col.replace("student_i_d", "student_id")
        return col

    df.columns = [normalize(str(c)) for c in df.columns]
    return df


# ---------------------------------------------------------------------------
# 8.3 Type conversion
# ---------------------------------------------------------------------------
def convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Cast columns to their proper numeric types where present."""
    df = df.copy()

    if "student_id" in df.columns:
        df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce").astype("Int64")
    if "age" in df.columns:
        df["age"] = pd.to_numeric(df["age"], errors="coerce")
    if "gpa" in df.columns:
        df["gpa"] = pd.to_numeric(df["gpa"], errors="coerce")
    if "attendance" in df.columns:
        df["attendance"] = pd.to_numeric(df["attendance"], errors="coerce")
    if "avg_score" in df.columns:
        df["avg_score"] = pd.to_numeric(df["avg_score"], errors="coerce")

    return df


# ---------------------------------------------------------------------------
# 8.2 Missing value handling
# ---------------------------------------------------------------------------
def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing values using a documented, field-specific strategy.

    Strategy (also documented in README.md, section "Data Quality"):
        - gpa:          fill with the column MEDIAN.
                         GPA tends to be skewed by a few very low/high
                         values, so the median is more robust than the
                         mean as a neutral "typical student" estimate.
        - attendance:   fill with a fixed BUSINESS RULE of 75 (the
                         minimum "Good" threshold), a deliberately
                         conservative assumption rather than guessing.
        - age:          left as missing here; out-of-range/missing age
                         is a business-rule violation handled by the
                         validation stage (rejected, not guessed).
        - text columns: left as missing; a student record without a
                         name/city is a data problem to flag, not to
                         paper over with a fabricated value.
    """
    df = df.copy()

    if "gpa" in df.columns and df["gpa"].isna().any():
        median_gpa = df["gpa"].median()
        n_missing = df["gpa"].isna().sum()
        df["gpa"] = df["gpa"].fillna(median_gpa)
        logger.info(
            f"Missing GPA: filled {n_missing} value(s) with column median ({median_gpa:.2f})"
        )

    if "attendance" in df.columns and df["attendance"].isna().any():
        default_attendance = 75
        n_missing = df["attendance"].isna().sum()
        df["attendance"] = df["attendance"].fillna(default_attendance)
        logger.info(
            f"Missing Attendance: filled {n_missing} value(s) using business rule ({default_attendance})"
        )

    return df


# ---------------------------------------------------------------------------
# 8.4 Derived columns
# ---------------------------------------------------------------------------
def _performance_level(gpa) -> str:
    if pd.isna(gpa):
        return "Unknown"
    if gpa >= 3.5:
        return "Excellent"
    if gpa >= 3.0:
        return "Very Good"
    if gpa >= 2.5:
        return "Good"
    if gpa >= 2.0:
        return "Acceptable"
    return "At Risk"


def _attendance_status(attendance) -> str:
    if pd.isna(attendance):
        return "Unknown"
    return "Good" if attendance >= 75 else "Low"


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add the two required derived columns: performance_level, attendance_status."""
    df = df.copy()

    if "gpa" in df.columns:
        df["performance_level"] = df["gpa"].apply(_performance_level)
    if "attendance" in df.columns:
        df["attendance_status"] = df["attendance"].apply(_attendance_status)

    logger.info("Derived columns added: performance_level, attendance_status")
    return df


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Run the full transformation stage in order."""
    logger.info("Transformation started")
    df = standardize_column_names(df)
    df = convert_types(df)
    df = handle_missing_values(df)
    df = add_derived_columns(df)
    logger.info("Transformation completed")
    return df
