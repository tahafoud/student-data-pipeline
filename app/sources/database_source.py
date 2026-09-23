"""
database_source.py
-------------------
Data Source 3: academic/course data stored in a SQLite database
(courses + enrollments tables), joined on course_id and returned keyed
by student_id.
"""

import sqlite3
from pathlib import Path

import pandas as pd

from app.utils.exceptions import SourceExtractionError
from app.utils.logger import get_logger

logger = get_logger(__name__)

QUERY = """
    SELECT
        e.student_id,
        c.course_name AS course,
        e.score,
        e.semester
    FROM enrollments e
    JOIN courses c ON e.course_id = c.course_id
"""


def extract_database(db_path: str | Path) -> pd.DataFrame:
    """
    Extract enrollment/course data from the SQLite database.

    Raises:
        SourceExtractionError: if the database file is missing or the
            query fails.
    """
    db_path = Path(db_path)
    logger.info("Database extraction started")

    if not db_path.exists():
        # First run convenience: build the sample database automatically
        # instead of failing, so `python main.py` works out of the box.
        logger.warning(f"Database file not found, building it now: {db_path}")
        from database.build_database import build_database

        build_database(db_path)

    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query(QUERY, conn)
    except sqlite3.Error as exc:
        logger.error(f"Database query failed: {exc}")
        raise SourceExtractionError(f"Database query failed: {exc}") from exc
    finally:
        try:
            conn.close()
        except Exception:
            pass

    logger.info(f"Database records: {len(df)}")
    df["source"] = "DATABASE"
    return df
