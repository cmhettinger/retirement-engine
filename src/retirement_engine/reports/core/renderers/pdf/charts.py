from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Flowable, Paragraph

from retirement_engine.reports.core.branding import ReportTheme
from retirement_engine.reports.core.renderers.pdf.styles import ReportStyles

Number = int | float | Decimal


@dataclass(frozen=True, slots=True)
class ChartPoint:
    label: str
    value: Number


@dataclass(frozen=True, slots=True)
class ChartSeries:
    label: str
    points: tuple[ChartPoint, ...]


@dataclass(frozen=True, slots=True)
class ChartDimensions:
    width: float = 432.0
    height: float = 252.0
    left_padding: float = 54.0
    right_padding: float = 22.0
    top_padding: float = 34.0
    bottom_padding: float = 44.0

    @property
    def plot_width(self) -> float:
        return self.width - self.left_padding - self.right_padding

    @property
    def plot_height(self) -> float:
        return self.height - self.top_padding - self.bottom_padding


@dataclass(frozen=True, slots=True)
class BarChartSpec:
    title: str
    series: tuple[ChartSeries, ...]
    dimensions: ChartDimensions = ChartDimensions()
    value_axis_label: str | None = None


@dataclass(frozen=True, slots=True)
class LineChartSpec:
    title: str
    series: tuple[ChartSeries, ...]
    dimensions: ChartDimensions = ChartDimensions()
    value_axis_label: str | None = None


@dataclass(frozen=True, slots=True)
class PieChartSpec:
    title: str
    points: tuple[ChartPoint, ...]
    dimensions: ChartDimensions = ChartDimensions()


@dataclass(frozen=True, slots=True)
class GaugeChartSpec:
    title: str
    value: Number
    target: Number = 1
    maximum: Number = Decimal("1.5")
    dimensions: ChartDimensions = ChartDimensions(height=138.0, bottom_padding=28.0)
    value_label: str | None = None
    target_label: str = "Target"
    maximum_label: str | None = None


@dataclass(frozen=True, slots=True)
class ChartBlockSpec:
    image_path: Path
    caption: str | None = None
    caption_gap: float = 6.0
    allow_upscale: bool = False
    pad: float = 6.0


class ChartBlock(Flowable):  # type: ignore[misc]
    def __init__(self, spec: ChartBlockSpec, *, styles: ReportStyles) -> None:
        super().__init__()
        self.spec = spec
        self.styles = styles
        self._reader = ImageReader(str(spec.image_path))
        width, height = self._reader.getSize()
        self._image_width = float(width)
        self._image_height = float(height)
        self._draw_width = 0.0
        self._draw_height = 0.0
        self._caption: Paragraph | None = None
        self._caption_height = 0.0
        self._total_height = 0.0

    def wrap(self, availWidth: float, availHeight: float) -> tuple[float, float]:  # noqa: N802
        available_width = max(1.0, float(availWidth) - self.spec.pad)
        available_height = max(1.0, float(availHeight) - self.spec.pad)
        caption_gap = self.spec.caption_gap if self.spec.caption else 0.0

        self._caption = (
            Paragraph(self.spec.caption, self.styles.small) if self.spec.caption else None
        )
        self._caption_height = 0.0
        if self._caption:
            _, self._caption_height = self._caption.wrap(available_width, available_height)

        image_height = max(1.0, available_height - self._caption_height - caption_gap)
        scale = min(available_width / self._image_width, image_height / self._image_height)
        if not self.spec.allow_upscale:
            scale = min(scale, 1.0)

        self._draw_width = self._image_width * scale
        self._draw_height = self._image_height * scale
        self._total_height = self._draw_height + caption_gap + self._caption_height
        return self._draw_width, self._total_height

    def draw(self) -> None:
        caption_gap = self.spec.caption_gap if self._caption else 0.0
        y = self._caption_height + caption_gap
        self.canv.drawImage(
            self._reader,
            0,
            y,
            width=self._draw_width,
            height=self._draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )
        if self._caption:
            self._caption.drawOn(self.canv, 0, 0)


def bar_chart(spec: BarChartSpec, *, theme: ReportTheme) -> Drawing:
    _require_series(spec.series)
    categories = _categories(spec.series)
    value_min, value_max = _value_range(spec.series)
    drawing = _base_drawing(spec.title, dimensions=spec.dimensions, theme=theme)
    chart = VerticalBarChart()
    _position_chart(chart, dimensions=spec.dimensions)
    chart.data = [_series_values(series) for series in spec.series]
    chart.categoryAxis.categoryNames = categories
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.angle = 30
    chart.valueAxis.valueMin = value_min
    chart.valueAxis.valueMax = value_max
    chart.valueAxis.visibleGrid = True
    chart.barSpacing = 2
    chart.groupSpacing = 10
    _apply_series_colors(chart.bars, count=len(spec.series), theme=theme)
    drawing.add(chart)
    _add_axis_label(drawing, spec.value_axis_label, dimensions=spec.dimensions, theme=theme)
    _add_legend(drawing, [series.label for series in spec.series], spec.dimensions, theme=theme)
    return drawing


def line_chart(spec: LineChartSpec, *, theme: ReportTheme) -> Drawing:
    _require_series(spec.series)
    categories = _categories(spec.series)
    value_min, value_max = _value_range(spec.series)
    drawing = _base_drawing(spec.title, dimensions=spec.dimensions, theme=theme)
    chart = HorizontalLineChart()
    _position_chart(chart, dimensions=spec.dimensions)
    chart.data = [_series_values(series) for series in spec.series]
    chart.categoryAxis.categoryNames = categories
    chart.categoryAxis.labels.boxAnchor = "ne"
    chart.categoryAxis.labels.angle = 30
    chart.valueAxis.valueMin = value_min
    chart.valueAxis.valueMax = value_max
    chart.valueAxis.visibleGrid = True
    chart.joinedLines = True
    _apply_series_colors(chart.lines, count=len(spec.series), theme=theme)
    drawing.add(chart)
    _add_axis_label(drawing, spec.value_axis_label, dimensions=spec.dimensions, theme=theme)
    _add_legend(drawing, [series.label for series in spec.series], spec.dimensions, theme=theme)
    return drawing


def pie_chart(spec: PieChartSpec, *, theme: ReportTheme) -> Drawing:
    if not spec.points:
        raise ValueError("Pie chart requires at least one point.")

    dimensions = spec.dimensions
    drawing = _base_drawing(spec.title, dimensions=dimensions, theme=theme)
    pie = Pie()
    pie.width = min(dimensions.plot_width * 0.56, dimensions.plot_height)
    pie.height = pie.width
    pie.x = dimensions.left_padding
    pie.y = dimensions.bottom_padding
    pie.data = [_number(point.value) for point in spec.points]
    pie.labels = [point.label for point in spec.points]
    pie.sideLabels = True
    for index, color in enumerate(_palette(theme, len(spec.points))):
        pie.slices[index].fillColor = color
    drawing.add(pie)
    _add_legend(drawing, [point.label for point in spec.points], dimensions, theme=theme)
    return drawing


def gauge_chart(spec: GaugeChartSpec, *, theme: ReportTheme) -> Drawing:
    maximum = max(_number(spec.maximum), 1.0)
    target = min(max(_number(spec.target), 0.0), maximum)
    value = min(max(_number(spec.value), 0.0), maximum)
    dimensions = spec.dimensions
    drawing = _base_drawing(spec.title, dimensions=dimensions, theme=theme)

    bar_x = dimensions.left_padding
    bar_y = dimensions.bottom_padding + 28
    bar_width = dimensions.plot_width
    bar_height = 22
    fill_width = bar_width * (value / maximum)
    target_x = bar_x + (bar_width * (target / maximum))

    drawing.add(
        Rect(
            bar_x,
            bar_y,
            bar_width,
            bar_height,
            fillColor=theme.light_grey,
            strokeColor=theme.light_grey,
            strokeWidth=0.5,
        )
    )
    drawing.add(
        Rect(
            bar_x,
            bar_y,
            fill_width,
            bar_height,
            fillColor=theme.primary,
            strokeColor=theme.primary,
            strokeWidth=0.5,
        )
    )
    drawing.add(
        Line(
            target_x,
            bar_y - 5,
            target_x,
            bar_y + bar_height + 5,
            strokeColor=theme.dark_grey,
            strokeWidth=1,
        )
    )
    drawing.add(
        String(
            bar_x,
            bar_y + bar_height + 14,
            spec.value_label or f"{_number(spec.value) * 100:,.1f}%",
            fontName=theme.body_semibold_font,
            fontSize=12,
            fillColor=theme.dark_grey,
        )
    )
    drawing.add(
        String(
            target_x - 12,
            bar_y - 16,
            spec.target_label,
            fontName=theme.body_font,
            fontSize=7,
            fillColor=theme.dark_grey,
        )
    )
    drawing.add(
        String(
            bar_x,
            bar_y - 16,
            "0%",
            fontName=theme.body_font,
            fontSize=7,
            fillColor=theme.dark_grey,
        )
    )
    drawing.add(
        String(
            bar_x + bar_width - 34,
            bar_y - 16,
            spec.maximum_label or f"{maximum * 100:,.0f}% scale",
            fontName=theme.body_font,
            fontSize=7,
            fillColor=theme.dark_grey,
        )
    )
    return drawing


def _base_drawing(title: str, *, dimensions: ChartDimensions, theme: ReportTheme) -> Drawing:
    drawing = Drawing(dimensions.width, dimensions.height)
    drawing.add(
        String(
            dimensions.left_padding,
            dimensions.height - 16,
            title,
            fontName=theme.body_semibold_font,
            fontSize=11,
            fillColor=theme.dark_grey,
        )
    )
    drawing.add(
        Line(
            dimensions.left_padding,
            dimensions.height - 24,
            dimensions.width - dimensions.right_padding,
            dimensions.height - 24,
            strokeColor=theme.light_grey,
            strokeWidth=0.5,
        )
    )
    return drawing


def _position_chart(chart: Any, *, dimensions: ChartDimensions) -> None:
    positioned_chart = chart
    positioned_chart.x = dimensions.left_padding
    positioned_chart.y = dimensions.bottom_padding
    positioned_chart.width = dimensions.plot_width
    positioned_chart.height = dimensions.plot_height


def _add_axis_label(
    drawing: Drawing,
    label: str | None,
    *,
    dimensions: ChartDimensions,
    theme: ReportTheme,
) -> None:
    if not label:
        return
    drawing.add(
        String(
            dimensions.left_padding,
            dimensions.height - 29,
            label,
            fontName=theme.body_font,
            fontSize=8,
            fillColor=theme.dark_grey,
        )
    )


def _add_legend(
    drawing: Drawing,
    labels: list[str],
    dimensions: ChartDimensions,
    *,
    theme: ReportTheme,
) -> None:
    if len(labels) <= 1:
        return
    legend = Legend()
    legend.x = dimensions.left_padding
    legend.y = 8
    legend.fontName = theme.body_font
    legend.fontSize = 7
    legend.boxAnchor = "sw"
    legend.columnMaximum = 2
    legend.dx = 7
    legend.dy = 7
    legend.deltax = 80
    legend.deltay = 10
    legend.colorNamePairs = list(
        zip(_palette(theme, len(labels), hex_strings=True), labels, strict=True)
    )
    drawing.add(legend)


def _apply_series_colors(collection: Any, *, count: int, theme: ReportTheme) -> None:
    for index, color in enumerate(_palette(theme, count)):
        collection[index].fillColor = color
        collection[index].strokeColor = color


def _palette(
    theme: ReportTheme,
    count: int,
    *,
    hex_strings: bool = False,
) -> list[object]:
    base = [
        "#1F5D3A",
        "#3F8F64",
        "#2B2B2B",
        "#6FA987",
        "#8AA39B",
        "#C9C9C9",
        "#4E6E5D",
        "#7A8C84",
    ]
    palette = [
        theme.primary,
        theme.accent,
        theme.dark_grey,
        *[colors.HexColor(value) for value in base[3:]],
    ]
    values = [palette[index % len(palette)] for index in range(count)]
    if hex_strings:
        return [base[index % len(base)] for index in range(count)]
    return values


def _require_series(series: tuple[ChartSeries, ...]) -> None:
    if not series:
        raise ValueError("Chart requires at least one series.")
    if not series[0].points:
        raise ValueError("Chart requires at least one point.")
    expected = tuple(point.label for point in series[0].points)
    for item in series:
        labels = tuple(point.label for point in item.points)
        if labels != expected:
            raise ValueError("All chart series must use the same point labels.")


def _categories(series: tuple[ChartSeries, ...]) -> list[str]:
    return [point.label for point in series[0].points]


def _series_values(series: ChartSeries) -> tuple[float, ...]:
    return tuple(_number(point.value) for point in series.points)


def _value_range(series: tuple[ChartSeries, ...]) -> tuple[float, float]:
    values = [value for item in series for value in _series_values(item)]
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        if minimum == 0:
            return 0, 1
        padding = abs(minimum) * 0.1
        return minimum - padding, maximum + padding
    padding = (maximum - minimum) * 0.08
    return min(0, minimum - padding), max(0, maximum + padding)


def _number(value: Number) -> float:
    return float(value)
