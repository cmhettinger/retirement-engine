"""Reusable report rendering primitives for Retirement Engine."""

from retirement_engine.reports.core.artifacts import ReportArtifact
from retirement_engine.reports.core.contracts import (
    OutputFormat,
    RenderContext,
    Renderer,
    RenderResult,
    ReportMetadata,
)

__version__ = "0.1.0"

__all__ = [
    "OutputFormat",
    "Renderer",
    "RenderContext",
    "RenderResult",
    "ReportArtifact",
    "ReportMetadata",
    "__version__",
]
