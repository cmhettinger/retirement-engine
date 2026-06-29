from pathlib import Path

from retirement_engine.config import load_config
from retirement_engine.reports import render_retirement_summary_pdf
from retirement_engine.workbook import load_retirement_workbook


def test_render_retirement_summary_pdf_writes_pdf(tmp_path: Path) -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)
    output_path = tmp_path / "retirement-summary.pdf"

    result = render_retirement_summary_pdf(
        workbook,
        output_dir=tmp_path,
        output_path=output_path,
    )

    assert result.primary_artifact.path == output_path
    assert result.primary_artifact.media_type == "application/pdf"
    assert output_path.read_bytes().startswith(b"%PDF")
