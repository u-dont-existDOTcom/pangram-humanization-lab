from __future__ import annotations

from scripts.render_reader_visible import reader_visible_text


def test_reader_visible_text_strips_source_markup_and_keeps_visible_labels() -> None:
    source = """[NATIVE IMAGE — preserve from Substack source — https://example.com/image.png]

[Share](%%share_url%%)

# Heading One

A [linked phrase](https://example.com/path) with *italics*, **bold**, and ***voice***.

---

- first item
- second item

> quoted text

[NATIVE SUBSTACK PREVIEW — Somatic Modalities Strategic Sequencing Roadmap — https://example.com/card]

[NATIVE YOUTUBE — preserve from Substack source — videoId: abc123]

[NATIVE BUTTON — Subscribe now — %%checkout_url%%]
"""

    assert reader_visible_text(source) == (
        "Heading One A linked phrase with italics, bold, and voice. "
        "first item second item quoted text "
        "Somatic Modalities Strategic Sequencing Roadmap Subscribe now"
    )


def test_reader_visible_text_does_not_leak_link_destinations_or_native_ids() -> None:
    source = (
        "Read [this](https://secret.example/path?q=1). "
        "[NATIVE YOUTUBE — old source — videoId: QqP3p_ysd84]"
    )
    visible = reader_visible_text(source)
    assert visible == "Read this."
    assert "secret.example" not in visible
    assert "QqP3p_ysd84" not in visible


def test_reader_visible_text_collapses_whitespace_deterministically() -> None:
    source = "# A\n\nParagraph one.\n\n\n## B\nParagraph two.\n"
    assert reader_visible_text(source) == "A Paragraph one. B Paragraph two."
