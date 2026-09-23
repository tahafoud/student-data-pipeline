"""
integration.py
---------------
Data Integration stage (assignment section 9).

Merges the three cleaned sources into a single dataset using the
shared key `student_id`:

    CSV (identity)  +  API (gpa/attendance/status)  +  DATABASE (courses/scores)

The CSV source is treated as the "spine" of the integration: it is
the authoritative list of enrolled students. API and database data
are joined onto it with a LEFT JOIN, so a student who exists in the
CSV but is (for example) temporarily missing from the academic API
still appears in the integrated dataset — instead of silently
disappearing, as an INNER JOIN would cause.

Also implements the "Data Lineage" excellence requirement: a `source`
column records which of the three systems contributed to each row.
"""

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def _aggregate_database_records(db_df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse the per-enrollment database rows (one row per course) into
    one row per student: average score, number of courses, and a
    comma-separated course list.
    """
    if db_df.empty:
        return pd.DataFrame(columns=["student_id", "avg_score", "courses_count", "courses"])

    grouped = db_df.groupby("student_id").agg(
        avg_score=("score", "mean"),
        courses_count=("course", "count"),
        courses=("course", lambda s: ", ".join(sorted(set(s)))),
    ).reset_index()

    return grouped


def integrate_data(
    csv_data: pd.DataFrame, api_data: pd.DataFrame, database_data: pd.DataFrame
) -> pd.DataFrame:
    """Merge the three sources on student_id into one integrated dataset."""
    logger.info("Data integration started")

    csv_data = csv_data.copy()
    api_data = api_data.copy()
    database_data = database_data.copy()

    # Normalize the join key's dtype across sources (CSV is read as str,
    # the API/DB sources come back as numeric) so the merge below doesn't
    # fail on a str/int64 mismatch.
    for frame in (csv_data, api_data, database_data):
        if "student_id" in frame.columns:
            frame["student_id"] = pd.to_numeric(frame["student_id"], errors="coerce")

    db_agg = _aggregate_database_records(database_data)

    csv_cols = [c for c in csv_data.columns if c != "source"]
    api_cols = [c for c in api_data.columns if c != "source"]

    merged = csv_data[csv_cols].merge(
        api_data[api_cols], on="student_id", how="left", suffixes=("", "_api")
    )
    merged = merged.merge(db_agg, on="student_id", how="left")

    # --- Data Lineage: record which source(s) contributed to each row ---
    has_api = set(api_data["student_id"].dropna())
    has_db = set(db_agg["student_id"].dropna())

    def lineage(row):
        parts = ["CSV"]
        if row["student_id"] in has_api:
            parts.append("API")
        if row["student_id"] in has_db:
            parts.append("DATABASE")
        return "+".join(parts)

    merged["source"] = merged.apply(lineage, axis=1)

    logger.info(f"Data integration completed: {len(merged)} integrated record(s)")
    return merged
