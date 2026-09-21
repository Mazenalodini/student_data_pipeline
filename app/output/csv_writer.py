from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Any

import pandas as pd

from app.models import RejectedRecord


def write_dataframe(dataframe: pd.DataFrame, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_file, index=False)


def write_json(payload: Any, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


def write_rejected_records(
    records: Iterable[RejectedRecord],
    output_file: Path,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for record in records:
        rows.append(
            {
                "source": record.source,
                "record_type": record.record_type,
                "student_id": record.student_id,
                "error_reason": record.error_reason,
                "raw_record": json.dumps(
                    record.raw_record,
                    ensure_ascii=False,
                    default=str,
                ),
                "detected_at": record.detected_at,
            }
        )

    dataframe = pd.DataFrame(
        rows,
        columns=[
            "source",
            "record_type",
            "student_id",
            "error_reason",
            "raw_record",
            "detected_at",
        ],
    )
    dataframe.to_csv(output_file, index=False)
