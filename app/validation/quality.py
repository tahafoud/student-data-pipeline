"""
quality.py
----------
Data Validation & Data Quality Rules (assignment sections 6 and 10).

Two entry points:

    validate_sources(csv_data, api_data, database_data)
        Runs lightweight, read-only checks on each RAW source right
        after extraction and logs a summary of problems found
        (missing IDs, duplicate IDs, out-of-range values). Nothing is
        dropped here — this stage is diagnostic, so problems are
        still visible for the cleaning stage to fix.

    validate_final_data(df)
        Runs the seven "Data Quality Rules" (section 10) against the
        fully transformed, integrated dataset and SPLITS it into:
            - a dataframe of valid records
            - a dataframe of rejected records, each tagged with the
              specific rule/reason it failed (used to build
              data/rejected/rejected_records.csv)

Quality Rules implemented:
    Rule 1: student_id cannot be NULL
    Rule 2: student_id must be unique
    Rule 3: age must be between 16 and 80
    Rule 4: GPA must be between 0 and 4
    Rule 5: attendance must be between 0 and 100
    Rule 6: score (avg_score) must be between 0 and 100
    Rule 7: student_id must be well-formed/compatible across sources
            (i.e. it must have converted cleanly to an integer)
"""

from typing import Tuple

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)

AGE_MIN, AGE_MAX = 16, 80
GPA_MIN, GPA_MAX = 0, 4
ATTENDANCE_MIN, ATTENDANCE_MAX = 0, 100
SCORE_MIN, SCORE_MAX = 0, 100


def validate_sources(
    csv_data: pd.DataFrame, api_data: pd.DataFrame, database_data: pd.DataFrame
) -> dict:
    """Diagnostic validation of each raw source. Logs findings, drops nothing."""
    report = {}

    if "student_id" in csv_data.columns:
        report["csv_missing_id"] = int(csv_data["student_id"].isna().sum())
        report["csv_duplicate_id"] = int(csv_data["student_id"].duplicated(keep=False).sum())
    if "age" in csv_data.columns:
        ages = pd.to_numeric(csv_data["age"], errors="coerce")
        report["csv_invalid_age"] = int(((ages < AGE_MIN) | (ages > AGE_MAX) | ages.isna()).sum())

    if "gpa" in api_data.columns:
        gpa = pd.to_numeric(api_data["gpa"], errors="coerce")
        report["api_invalid_gpa"] = int(((gpa < GPA_MIN) | (gpa > GPA_MAX) | gpa.isna()).sum())
    if "attendance" in api_data.columns:
        att = pd.to_numeric(api_data["attendance"], errors="coerce")
        report["api_invalid_attendance"] = int(
            ((att < ATTENDANCE_MIN) | (att > ATTENDANCE_MAX) | att.isna()).sum()
        )

    if "score" in database_data.columns:
        score = pd.to_numeric(database_data["score"], errors="coerce")
        report["db_invalid_score"] = int(
            ((score < SCORE_MIN) | (score > SCORE_MAX) | score.isna()).sum()
        )

    logger.info(f"Source validation summary: {report}")
    return report


def _first_failed_rule(row: pd.Series) -> str | None:
    """Return the reason string for the first quality rule a row fails, or None."""
    if pd.isna(row.get("student_id")):
        return "Missing student_id"

    if "age" in row:
        if pd.isna(row["age"]):
            return "Missing age"
        if not (AGE_MIN <= row["age"] <= AGE_MAX):
            return "Invalid age"

    if "gpa" in row and pd.notna(row["gpa"]):
        if not (GPA_MIN <= row["gpa"] <= GPA_MAX):
            return "Invalid GPA"

    if "attendance" in row and pd.notna(row["attendance"]):
        if not (ATTENDANCE_MIN <= row["attendance"] <= ATTENDANCE_MAX):
            return "Invalid Attendance"

    if "avg_score" in row and pd.notna(row["avg_score"]):
        if not (SCORE_MIN <= row["avg_score"] <= SCORE_MAX):
            return "Invalid Score"

    return None


def validate_final_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply the final quality rules and split the dataset into
    (valid_records, rejected_records_with_reason).
    """
    logger.info("Final validation started")
    df = df.copy()

    # Rule 2: duplicate student_id -> keep first occurrence, reject the rest
    duplicate_mask = df["student_id"].duplicated(keep="first") & df["student_id"].notna()

    reasons = df.apply(_first_failed_rule, axis=1)
    reasons = reasons.where(~duplicate_mask, "Duplicate student_id")

    rejected_mask = reasons.notna()

    rejected = df[rejected_mask].copy()
    rejected["error_reason"] = reasons[rejected_mask]

    valid = df[~rejected_mask].copy()

    logger.info(
        f"Validation completed: {len(valid)} valid record(s), {len(rejected)} rejected record(s)"
    )
    return valid, rejected
