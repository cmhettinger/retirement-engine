from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reportlab.platypus import BaseDocTemplate, PageTemplate

from retirement_engine.reports.core.branding import BrandingConfig, register_brand_fonts


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    title: str
    author: str = "Retirement Engine"
    subject: str | None = None
    creator: str = "retirement-engine-reports"
    keywords: tuple[str, ...] = ()


PdfDocument = BaseDocTemplate


class ReportDocTemplate(BaseDocTemplate):  # type: ignore[misc]
    """Base PDF document with table-of-contents and outline notifications."""

    def afterFlowable(self, flowable: object) -> None:  # noqa: N802
        toc_entry = getattr(flowable, "_retirement_engine_toc_entry", None)
        if toc_entry is None:
            return

        level, text, bookmark = toc_entry
        if bookmark:
            self.canv.bookmarkPage(bookmark)
            self.canv.addOutlineEntry(text, bookmark, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, bookmark))


def make_doc(
    *,
    out_path: Path,
    templates: Sequence[PageTemplate],
    spec: DocumentSpec,
) -> BaseDocTemplate:
    out_path = Path(out_path).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = ReportDocTemplate(str(out_path))
    doc.title = spec.title
    doc.author = spec.author
    doc.creator = spec.creator
    if spec.subject:
        doc.subject = spec.subject
    if spec.keywords:
        doc.keywords = ", ".join(spec.keywords)
    doc.addPageTemplates(list(templates))
    return doc


def build_pdf(
    *,
    doc: BaseDocTemplate,
    story: Sequence[object],
    out_path: Path,
    branding: BrandingConfig | None = None,
) -> Path:
    register_brand_fonts(branding)
    resolved = Path(out_path).expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    build_story = list(story)
    if any(_uses_table_of_contents(flowable) for flowable in build_story):
        doc.multiBuild(build_story)
    else:
        doc.build(build_story)
    return resolved


def _uses_table_of_contents(flowable: Any) -> bool:
    return bool(flowable.__class__.__name__ == "TableOfContents")
