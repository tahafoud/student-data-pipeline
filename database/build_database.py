"""
build_database.py
------------------
Utility script that (re)creates the SQLite database used as the third
data source for the pipeline (database/students.db).

It creates two tables:
    - courses:      course_id, course_name, credit_hours
    - enrollments:  student_id, course_id, semester, score

Run directly:
    python database/build_database.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "students.db"

COURSES = [
    (1, "Introduction to Programming", 3),
    (2, "Data Structures", 3),
    (3, "Database Systems", 4),
    (4, "Machine Learning", 4),
    (5, "Computer Networks", 3),
]

# (student_id, course_id, semester, score)
# Intentionally includes a few invalid / edge-case scores to be caught
# by the validation stage (score must be 0-100).
ENROLLMENTS = [
    (1001, 1, "Fall2025", 88),
    (1001, 3, "Fall2025", 91),
    (1002, 2, "Fall2025", 76),
    (1002, 4, "Fall2025", 95),
    (1003, 1, "Fall2025", 63),
    (1004, 2, "Fall2025", 58),
    (1005, 3, "Fall2025", 72),
    (1006, 4, "Fall2025", 84),
    (1007, 1, "Fall2025", 105),   # invalid: > 100
    (1008, 2, "Fall2025", 67),
    (1009, 3, "Fall2025", 79),
    (1010, 1, "Fall2025", 90),
    (1011, 4, "Fall2025", 55),
    (1012, 2, "Fall2025", -10),   # invalid: < 0
    (1013, 5, "Fall2025", 81),
    (1014, 1, "Fall2025", 70),
    (1015, 3, "Fall2025", 66),
    (1016, 4, "Fall2025", 89),
    (1017, 5, "Fall2025", 74),
    (1018, 2, "Fall2025", 92),
    (1019, 1, "Fall2025", 60),
]


def build_database(db_path: Path = DB_PATH) -> None:
    """Create (or refresh) the SQLite database with sample data."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS courses")
    cur.execute("DROP TABLE IF EXISTS enrollments")

    cur.execute(
        """
        CREATE TABLE courses (
            course_id     INTEGER PRIMARY KEY,
            course_name   TEXT NOT NULL,
            credit_hours  INTEGER NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE enrollments (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id  INTEGER NOT NULL,
            course_id   INTEGER NOT NULL,
            semester    TEXT NOT NULL,
            score       REAL,
            FOREIGN KEY (course_id) REFERENCES courses (course_id)
        )
        """
    )

    cur.executemany(
        "INSERT INTO courses (course_id, course_name, credit_hours) VALUES (?, ?, ?)",
        COURSES,
    )
    cur.executemany(
        "INSERT INTO enrollments (student_id, course_id, semester, score) VALUES (?, ?, ?, ?)",
        ENROLLMENTS,
    )

    conn.commit()
    conn.close()
    print(f"Database created at: {db_path}")


if __name__ == "__main__":
    build_database()
