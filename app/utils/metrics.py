"""
metrics.py
----------
Pipeline Metrics (excellence requirement #4): tracks record counts and
processing time and prints a summary block like:

    ----------------------------------------
    PIPELINE EXECUTION SUMMARY
    ----------------------------------------
    CSV Records       : 100
    API Records       : 100
    Database Records  : 250
    Integrated Records: 100
    Valid Records     : 92
    Rejected Records  : 8
    Duplicate Records : 5
    Processing Time   : 2.31 seconds
    ----------------------------------------
"""

import time
from dataclasses import dataclass, field


@dataclass
class PipelineMetrics:
    csv_records: int = 0
    api_records: int = 0
    database_records: int = 0
    integrated_records: int = 0
    valid_records: int = 0
    rejected_records: int = 0
    duplicate_records: int = 0
    _start_time: float = field(default_factory=time.perf_counter, repr=False)
    processing_time: float = 0.0

    def stop_timer(self) -> None:
        self.processing_time = round(time.perf_counter() - self._start_time, 2)

    def summary(self) -> str:
        width = 40
        lines = [
            "-" * width,
            "PIPELINE EXECUTION SUMMARY",
            "-" * width,
            f"CSV Records       : {self.csv_records}",
            f"API Records       : {self.api_records}",
            f"Database Records  : {self.database_records}",
            f"Integrated Records: {self.integrated_records}",
            f"Valid Records     : {self.valid_records}",
            f"Rejected Records  : {self.rejected_records}",
            f"Duplicate Records : {self.duplicate_records}",
            f"Processing Time   : {self.processing_time} seconds",
            "-" * width,
        ]
        return "\n".join(lines)
