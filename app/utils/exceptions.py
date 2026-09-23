"""Custom exception types used across the pipeline."""


class PipelineError(Exception):
    """Base class for all pipeline-related errors."""


class SourceExtractionError(PipelineError):
    """Raised when a data source (CSV, API, DB) fails to be extracted."""


class DataQualityError(PipelineError):
    """Raised when data fails a validation rule that halts the pipeline."""
