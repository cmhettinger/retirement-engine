from pathlib import Path

from retirement_engine.reports.core.branding import BrandingConfig, ReportTheme


def test_report_theme_uses_retirement_engine_brand_colors() -> None:
    theme = ReportTheme()

    assert theme.primary.hexval().lower() == "0x1f5d3a"
    assert theme.accent.hexval().lower() == "0x3f8f64"
    assert theme.light_grey.hexval().lower() == "0xc9c9c9"
    assert theme.dark_grey.hexval().lower() == "0x2b2b2b"


def test_default_logo_path_uses_green_variant(tmp_path: Path) -> None:
    branding = BrandingConfig(root=tmp_path)

    assert (
        branding.logo_path()
        == tmp_path / "logo" / "green" / "256h" / "logo-horizontal.png"
    )
