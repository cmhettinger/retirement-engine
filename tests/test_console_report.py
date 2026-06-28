from retirement_engine.config import load_config
from retirement_engine.reports import render_console_summary_report
from retirement_engine.workbook import load_retirement_workbook


def test_render_console_summary_report_includes_key_sections() -> None:
    config = load_config()
    workbook = load_retirement_workbook(config.default_workbook)

    report = render_console_summary_report(workbook)

    assert report.startswith("Retirement Summary Report\n=========================\n")
    assert "People:\n  Han Solo\n  Leia Organa" in report
    assert "Annual spending need:        $238,931" in report
    assert "Monthly spending need:       $19,911" in report
    assert "Annual withdrawal need:      $44,831" in report
    assert "Status:                      on track" in report
    assert "Planned retirement year:     2035" in report
    assert "Earliest viable year:        2026" in report
    assert "Surplus / shortfall:         $2,372,554" in report
    assert "Policies needing review:     2" in report
    assert "Warnings\n--------" in report
    assert (
        "- Estimated retirement income is below projected spending need before portfolio "
        "withdrawals."
    ) in report
    assert "Next Steps\n----------" in report
    assert "- Stress-test the on-track result with future Monte Carlo scenarios." in report
