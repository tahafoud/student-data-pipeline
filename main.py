"""
main.py
-------
Entry point for the Student Data Pipeline.

Orchestrates the full ETL flow:

    Extract (CSV, API, SQLite)
        -> Validate sources (diagnostic)
        -> Clean each source
        -> Integrate (merge on student_id)
        -> Transform (types, missing values, derived columns)
        -> Validate final data (quality rules -> valid / rejected)
        -> Load (final_dataset.csv, rejected_records.csv)

Run:
    python main.py
"""

from app.output.csv_writer import save_processed_data, save_rejected_data
from app.sources.api_source import extract_api
from app.sources.csv_source import extract_csv
from app.sources.database_source import extract_database
from app.transformation.cleaner import clean_api_data, clean_csv_data, clean_database_data
from app.transformation.integration import integrate_data
from app.transformation.transformer import transform_data
from app.utils.config_loader import load_config, resolve_path
from app.utils.logger import get_logger
from app.utils.metrics import PipelineMetrics
from app.validation.quality import validate_final_data, validate_sources

logger = get_logger(__name__)


def run_pipeline():
    config = load_config()
    metrics = PipelineMetrics()

    # ---------------------------------------------------------------
    # Extract
    # ---------------------------------------------------------------
    csv_data = extract_csv(resolve_path(config["sources"]["csv"]["path"]))
    metrics.csv_records = len(csv_data)

    api_cfg = config["sources"]["api"]
    api_data = extract_api(
        base_url=api_cfg.get("base_url"),
        endpoint=api_cfg.get("endpoint", "/api/academic"),
        use_mock=api_cfg.get("use_mock", True),
        timeout_seconds=api_cfg.get("timeout_seconds", 5),
        max_retries=api_cfg.get("max_retries", 3),
    )
    metrics.api_records = len(api_data)

    database_data = extract_database(resolve_path(config["sources"]["database"]["path"]))
    metrics.database_records = len(database_data)

    # ---------------------------------------------------------------
    # Validate sources (diagnostic — logs issues, changes nothing)
    # ---------------------------------------------------------------
    validate_sources(csv_data, api_data, database_data)

    # ---------------------------------------------------------------
    # Clean each source
    # ---------------------------------------------------------------
    csv_data = clean_csv_data(csv_data)
    api_data = clean_api_data(api_data)
    database_data = clean_database_data(database_data)

    duplicates_removed = metrics.csv_records - len(csv_data)

    # ---------------------------------------------------------------
    # Integrate
    # ---------------------------------------------------------------
    integrated_data = integrate_data(csv_data, api_data, database_data)
    metrics.integrated_records = len(integrated_data)

    # ---------------------------------------------------------------
    # Transform
    # ---------------------------------------------------------------
    transformed_data = transform_data(integrated_data)

    # ---------------------------------------------------------------
    # Final validation -> valid / rejected split
    # ---------------------------------------------------------------
    valid_data, rejected_data = validate_final_data(transformed_data)
    metrics.valid_records = len(valid_data)
    metrics.rejected_records = len(rejected_data)
    metrics.duplicate_records = duplicates_removed + int(
        (rejected_data.get("error_reason") == "Duplicate student_id").sum()
        if "error_reason" in rejected_data.columns
        else 0
    )

    # ---------------------------------------------------------------
    # Load
    # ---------------------------------------------------------------
    save_processed_data(valid_data, resolve_path(config["output"]["processed_path"]))
    save_rejected_data(rejected_data, resolve_path(config["output"]["rejected_path"]))

    metrics.stop_timer()
    print(metrics.summary())
    logger.info("Pipeline run finished successfully")

    return valid_data, rejected_data, metrics


if __name__ == "__main__":
    run_pipeline()
