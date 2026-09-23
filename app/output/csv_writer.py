"""
csv_writer.py
-------------
Load stage (assignment section 12): writes the final, clean dataset
and the rejected-records report to disk.
"""

from pathlib import Path

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def save_processed_data(df: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Final dataset created: {output_path} ({len(df)} record(s))")


def save_rejected_data(df: pd.DataFrame, output_path: str | Path) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if "student_id" in df.columns and "error_reason" in df.columns:
        df = df[["student_id", "error_reason"]]

    df.to_csv(output_path, index=False)
    logger.info(f"Rejected records saved: {output_path} ({len(df)} record(s))")
