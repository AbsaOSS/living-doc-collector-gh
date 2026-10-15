"""Tests for recognizing living-documentation headers."""

from doc_source.collector import _has_living_doc_header


def test_body_string_marker_passes_the_file_wide_filter() -> None:
    """A marker in body text passes the current file-wide marker check."""
    source = """/**
 * Helper module.
 */
const marker = "LIVING DOC";
"""
    assert _has_living_doc_header(source)
