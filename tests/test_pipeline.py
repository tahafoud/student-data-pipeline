"""
test_pipeline.py
-----------------
Covers the 8 tests required by the assignment (section 18):

    Test 1: Was the CSV loaded?
    Test 2: Was the API connection successful?
    Test 3: Was data extracted from SQLite?
    Test 4: Were duplicates removed?
    Test 5: Were missing values handled?
    Test 6: Were invalid records rejected?
    Test 7: Were the sources integrated successfully?
    Test 8: Was final_dataset.csv created?

Run with:
    python -m unittest discover -s tests
or, if pytest is installed:
    pytest tests/
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd  # noqa: E402

from app.sources.api_source import extract_api  # noqa: E402
from app.sources.csv_source import extract_csv  # noqa: E402
from app.sources.database_source import extract_database  # noqa: E402
from app.transformation.cleaner import clean_csv_data  # noqa: E402
from app.transformation.integration import integrate_data  # noqa: E402
from app.transformation.transformer import transform_data  # noqa: E402
from app.validation.quality import validate_final_data  # noqa: E402
from database.build_database import build_database  # noqa: E402


class PipelineTestCase(unittest.TestCase):
    """Shared fixtures: a temp DB and the real sample CSV/API sources."""

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = Path(tempfile.mkdtemp())
        cls.db_path = cls.tmp_dir / "students.db"
        build_database(cls.db_path)

        cls.csv_path = PROJECT_ROOT / "data" / "raw" / "students.csv"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir, ignore_errors=True)

    # ---- Test 1: CSV loaded -------------------------------------------------
    def test_1_csv_is_loaded(self):
        df = extract_csv(self.csv_path)
        self.assertGreater(len(df), 0)
        self.assertIn("student_id", df.columns)

    # ---- Test 2: API connection successful ----------------------------------
    def test_2_api_connection_successful(self):
        df = extract_api(use_mock=True)
        self.assertGreater(len(df), 0)
        self.assertIn("gpa", df.columns)

    # ---- Test 3: data extracted from SQLite ---------------------------------
    def test_3_sqlite_extraction(self):
        df = extract_database(self.db_path)
        self.assertGreater(len(df), 0)
        self.assertIn("student_id", df.columns)
        self.assertIn("score", df.columns)

    # ---- Test 4: duplicates removed -----------------------------------------
    def test_4_duplicates_removed(self):
        raw = extract_csv(self.csv_path)
        n_duplicate_ids_before = raw["student_id"].duplicated().sum()
        self.assertGreater(n_duplicate_ids_before, 0, "fixture should contain a duplicate")

        cleaned = clean_csv_data(raw)
        self.assertEqual(cleaned["student_id"].duplicated().sum(), 0)

    # ---- Test 5: missing values handled -------------------------------------
    def test_5_missing_values_handled(self):
        csv_data = clean_csv_data(extract_csv(self.csv_path))
        api_data = extract_api(use_mock=True)
        database_data = extract_database(self.db_path)

        integrated = integrate_data(csv_data, api_data, database_data)
        transformed = transform_data(integrated)

        self.assertEqual(transformed["gpa"].isna().sum(), 0)
        self.assertEqual(transformed["attendance"].isna().sum(), 0)

    # ---- Test 6: invalid records rejected -----------------------------------
    def test_6_invalid_records_rejected(self):
        csv_data = clean_csv_data(extract_csv(self.csv_path))
        api_data = extract_api(use_mock=True)
        database_data = extract_database(self.db_path)

        integrated = integrate_data(csv_data, api_data, database_data)
        transformed = transform_data(integrated)
        valid, rejected = validate_final_data(transformed)

        self.assertGreater(len(rejected), 0)
        self.assertIn("error_reason", rejected.columns)
        # every valid record must satisfy the age rule
        self.assertTrue(((valid["age"] >= 16) & (valid["age"] <= 80)).all())

    # ---- Test 7: sources integrated successfully ----------------------------
    def test_7_sources_integrated(self):
        csv_data = clean_csv_data(extract_csv(self.csv_path))
        api_data = extract_api(use_mock=True)
        database_data = extract_database(self.db_path)

        integrated = integrate_data(csv_data, api_data, database_data)

        for col in ("student_id", "gpa", "avg_score", "source"):
            self.assertIn(col, integrated.columns)
        self.assertLessEqual(len(integrated), len(csv_data))

    # ---- Test 8: final_dataset.csv created ----------------------------------
    def test_8_final_dataset_created(self):
        from app.output.csv_writer import save_processed_data

        csv_data = clean_csv_data(extract_csv(self.csv_path))
        api_data = extract_api(use_mock=True)
        database_data = extract_database(self.db_path)

        integrated = integrate_data(csv_data, api_data, database_data)
        transformed = transform_data(integrated)
        valid, _ = validate_final_data(transformed)

        out_path = self.tmp_dir / "final_dataset.csv"
        save_processed_data(valid, out_path)

        self.assertTrue(out_path.exists())
        written_back = pd.read_csv(out_path)
        self.assertEqual(len(written_back), len(valid))


if __name__ == "__main__":
    unittest.main()
