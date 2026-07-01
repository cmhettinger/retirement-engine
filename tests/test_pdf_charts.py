from pathlib import Path

import pytest
from reportlab.graphics.shapes import Drawing
from reportlab.platypus import SimpleDocTemplate

from retirement_engine.reports.core.branding import register_brand_fonts
from retirement_engine.reports.core.renderers.pdf import (
    BarChartSpec,
    ChartPoint,
    ChartSeries,
    GaugeChartSpec,
    LineChartSpec,
    PieChartSpec,
    bar_chart,
    gauge_chart,
    line_chart,
    pie_chart,
)


def test_native_bar_line_and_pie_charts_render_to_pdf(tmp_path: Path) -> None:
    theme = register_brand_fonts()
    series = (
        ChartSeries(
            "Income",
            (
                ChartPoint("2026", 100),
                ChartPoint("2027", 115),
                ChartPoint("2028", 130),
            ),
        ),
        ChartSeries(
            "Expenses",
            (
                ChartPoint("2026", 90),
                ChartPoint("2027", 105),
                ChartPoint("2028", 125),
            ),
        ),
    )

    drawings = [
        bar_chart(BarChartSpec(title="Income vs expenses", series=series), theme=theme),
        line_chart(LineChartSpec(title="Portfolio trend", series=series), theme=theme),
        gauge_chart(GaugeChartSpec(title="Funded ratio", value=1.12), theme=theme),
        pie_chart(
            PieChartSpec(
                title="Asset mix",
                points=(
                    ChartPoint("Pre-tax", 60),
                    ChartPoint("Roth", 25),
                    ChartPoint("Taxable", 15),
                ),
            ),
            theme=theme,
        ),
    ]

    assert all(isinstance(drawing, Drawing) for drawing in drawings)

    output_path = tmp_path / "charts.pdf"
    SimpleDocTemplate(str(output_path)).build(drawings)

    assert output_path.read_bytes().startswith(b"%PDF")


def test_chart_series_must_use_matching_labels() -> None:
    theme = register_brand_fonts()
    spec = BarChartSpec(
        title="Mismatched chart",
        series=(
            ChartSeries("First", (ChartPoint("A", 1), ChartPoint("B", 2))),
            ChartSeries("Second", (ChartPoint("A", 1), ChartPoint("C", 2))),
        ),
    )

    with pytest.raises(ValueError, match="same point labels"):
        bar_chart(spec, theme=theme)
