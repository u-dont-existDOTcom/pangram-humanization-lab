from __future__ import annotations

from pangram_lab.idiolect_transformation_sensitivity import (
    _git_blob_sha1,
    _text_sha256,
    extract_first_paragraph_under_heading,
)


def test_extract_first_paragraph_under_exact_heading():
    text = """# Top\n\n### Alpha\n\nFirst line.\nSecond line.\n\nOther text.\n\n### Beta\n\nBeta paragraph.\n"""
    assert extract_first_paragraph_under_heading(text, "Alpha") == "First line. Second line."
    assert extract_first_paragraph_under_heading(text, "Beta") == "Beta paragraph."


def test_extract_heading_is_exact():
    text = "### Alpha extended\n\nWrong.\n\n### Alpha\n\nRight.\n"
    assert extract_first_paragraph_under_heading(text, "Alpha") == "Right."


def test_hash_helpers_are_stable():
    assert _text_sha256("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert _git_blob_sha1(b"test\n") == "9daeafb9864cf43055ae93beb0afd6c7d144bfa4"
