"""Validation for Retirement Engine workbooks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from retirement_engine.config import AppConfig
from retirement_engine.workbook.reader import (
    RetirementWorkbook,
    WorkbookCellValue,
    load_retirement_workbook,
)

ValidationStatus = Literal["passed", "failed"]

STABLE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:[._][a-z0-9]+)*$")
YES_NO_FIELDS = {
    "Budget": "Must Pay",
    "Income": "Taxable",
}
WORKBOOK_VERSION_ROW_ID = "system.workbook.version"


@dataclass(frozen=True)
class WorkbookSchemaSheet:
    name: str
    headers: tuple[str, ...]
    required_row_ids: tuple[str, ...]


@dataclass(frozen=True)
class WorkbookSchema:
    sheets: tuple[WorkbookSchemaSheet, ...]


@dataclass(frozen=True)
class ValidationFailure:
    code: str
    message: str
    sheet: str | None = None
    row_number: int | None = None
    column: str | None = None
    row_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "sheet": self.sheet,
            "row_number": self.row_number,
            "column": self.column,
            "row_id": self.row_id,
        }


@dataclass(frozen=True)
class WorkbookValidationReport:
    status: ValidationStatus
    workbook: Path
    failures: tuple[ValidationFailure, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "workbook": str(self.workbook),
            "summary": {
                "failure_count": len(self.failures),
            },
            "failures": [failure.to_dict() for failure in self.failures],
        }


def load_schema_from_template(template_path: str | Path) -> WorkbookSchema:
    """Load required workbook structure from the checked-in template workbook."""

    template = load_retirement_workbook(template_path)
    return WorkbookSchema(
        sheets=tuple(
            WorkbookSchemaSheet(
                name=sheet.name,
                headers=sheet.headers,
                required_row_ids=tuple(row_id for row_id in sheet.rows_by_id),
            )
            for sheet in template.sheets.values()
        )
    )


def validate_retirement_workbook(
    workbook: RetirementWorkbook,
    config: AppConfig,
    *,
    schema: WorkbookSchema | None = None,
) -> WorkbookValidationReport:
    """Validate workbook structure and user-entered classification fields."""

    validation_schema = schema or load_schema_from_template(
        config.project_root / "resources" / "workbooks" / "template.xlsx"
    )
    failures: list[ValidationFailure] = []

    failures.extend(_validate_schema(workbook, validation_schema))
    failures.extend(_validate_workbook_version(workbook, config))
    failures.extend(_validate_stable_ids(workbook))
    failures.extend(_validate_yes_no_fields(workbook))

    return WorkbookValidationReport(
        status="failed" if failures else "passed",
        workbook=workbook.path,
        failures=tuple(failures),
    )


def _validate_schema(
    workbook: RetirementWorkbook,
    schema: WorkbookSchema,
) -> tuple[ValidationFailure, ...]:
    failures: list[ValidationFailure] = []

    for expected_sheet in schema.sheets:
        sheet = workbook.sheets.get(expected_sheet.name)
        if sheet is None:
            failures.append(
                ValidationFailure(
                    code="missing_required_sheet",
                    message=f"Missing required sheet: {expected_sheet.name}.",
                    sheet=expected_sheet.name,
                )
            )
            continue

        for header in expected_sheet.headers:
            if header not in sheet.headers:
                failures.append(
                    ValidationFailure(
                        code="missing_required_column",
                        message=f"Sheet {sheet.name} is missing required column: {header}.",
                        sheet=sheet.name,
                        column=header,
                    )
                )

        row_ids = {row.row_id for row in sheet.rows if row.row_id is not None}
        for row_id in expected_sheet.required_row_ids:
            if row_id not in row_ids:
                failures.append(
                    ValidationFailure(
                        code="missing_required_row",
                        message=f"Sheet {sheet.name} is missing required row ID: {row_id}.",
                        sheet=sheet.name,
                        row_id=row_id,
                    )
                )

    return tuple(failures)


def _validate_workbook_version(
    workbook: RetirementWorkbook,
    config: AppConfig,
) -> tuple[ValidationFailure, ...]:
    assumptions = workbook.sheets.get("Assumptions")
    if assumptions is None:
        return ()

    version_row = assumptions.rows_by_id.get(WORKBOOK_VERSION_ROW_ID)
    if version_row is None:
        return ()

    workbook_version = _display_value(version_row.values.get("Value"))
    if workbook_version == config.supported_workbook_version:
        return ()

    return (
        ValidationFailure(
            code="workbook_version_mismatch",
            message=(
                "Workbook version "
                f"{workbook_version or '<blank>'} does not match supported version "
                f"{config.supported_workbook_version}."
            ),
            sheet="Assumptions",
            row_number=version_row.row_number,
            column="Value",
            row_id=WORKBOOK_VERSION_ROW_ID,
        ),
    )


def _validate_stable_ids(workbook: RetirementWorkbook) -> tuple[ValidationFailure, ...]:
    failures: list[ValidationFailure] = []
    seen: dict[str, tuple[str, int]] = {}

    for sheet in workbook.sheets.values():
        if "ID" not in sheet.headers:
            continue

        for row in sheet.rows:
            row_id = _display_value(row.values.get("ID"))
            if row_id is None:
                failures.append(
                    ValidationFailure(
                        code="missing_stable_id",
                        message=f"Sheet {sheet.name} row {row.row_number} is missing a stable ID.",
                        sheet=sheet.name,
                        row_number=row.row_number,
                        column="ID",
                    )
                )
                continue

            if STABLE_ID_PATTERN.fullmatch(row_id) is None:
                failures.append(
                    ValidationFailure(
                        code="invalid_stable_id",
                        message=(
                            f"Sheet {sheet.name} row {row.row_number} has invalid stable ID: "
                            f"{row_id}."
                        ),
                        sheet=sheet.name,
                        row_number=row.row_number,
                        column="ID",
                        row_id=row_id,
                    )
                )

            first_seen = seen.get(row_id)
            if first_seen is not None:
                first_sheet, first_row_number = first_seen
                failures.append(
                    ValidationFailure(
                        code="duplicate_stable_id",
                        message=(
                            f"Duplicate stable ID {row_id} appears on {sheet.name} row "
                            f"{row.row_number}; first seen on {first_sheet} row {first_row_number}."
                        ),
                        sheet=sheet.name,
                        row_number=row.row_number,
                        column="ID",
                        row_id=row_id,
                    )
                )
            else:
                seen[row_id] = (sheet.name, row.row_number)

    return tuple(failures)


def _validate_yes_no_fields(workbook: RetirementWorkbook) -> tuple[ValidationFailure, ...]:
    failures: list[ValidationFailure] = []

    for sheet_name, column in YES_NO_FIELDS.items():
        sheet = workbook.sheets.get(sheet_name)
        if sheet is None or column not in sheet.headers:
            continue

        for row in sheet.rows:
            value = _display_value(row.values.get(column))
            if value is None or value in {"Yes", "No"}:
                continue

            failures.append(
                ValidationFailure(
                    code="invalid_yes_no",
                    message=(
                        f"Sheet {sheet.name} row {row.row_number} column {column} must be "
                        f"Yes, No, or blank; found {value}."
                    ),
                    sheet=sheet.name,
                    row_number=row.row_number,
                    column=column,
                    row_id=row.row_id,
                )
            )

    return tuple(failures)


def _display_value(value: WorkbookCellValue) -> str | None:
    if value is None:
        return None

    text = str(value).strip()
    return text or None
