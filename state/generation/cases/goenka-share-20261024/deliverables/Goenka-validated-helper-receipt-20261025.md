# Goenka article — validated clipboard transfer receipt

Date: 2026-10-25. **Completed static source, editorial-delta, and canonical-generator verification.** A real Opera-to-disposable-Substack-draft test remains pending. Nothing was pasted or published by this worker.

## Authoritative inputs and output status

- Source supplied directly by Joel: raw `div[data-testid="editor"].tiptap.ProseMirror` HTML, 63,706 UTF-8 bytes, SHA-256 `a85af3ccd8dfc7c7a10699925fd8085cb2d35784b13afee66044be5b0c35199c`.
- Target: existing Goenka article editing session; **research working copy**, not a registered article master.
- Approved final archival HTML: 63,797 bytes; SHA-256 `b285c6e20f3a8cd953c27664a948b53294ead762d64fdc66eb7a3fc6baeec819`.
- Exact user-local downloaded helper: `~/Téléchargements/Goenka-validated-clipboard-20261025.html`; SHA-256 `cf98483591a75136764bf1a20f706bfd08af46ccaddd0342c55ca3e2e7cc9788`; 50,236 UTF-8 bytes.
- User-local archival source and report: `~/Téléchargements/Goenka-archival-approved-20261025.html` and `~/Téléchargements/Goenka-validated-transfer-report-20261025.md`.
- Embedded manifest format `joel-substack-transfer-helper-v4`; source SHA-256 as above; editor body SHA-256 `f8823463d0004ccb696fa2a9ab91c145ca54c836a835faf3497d10448600c829`; compatibility profile SHA-256 `c58bf6928274eb9734194c280a8a5f3b53be50d0e913e7cfb24c23593af05734`; payload SHA-256 `4fa5f767d863904c79d53b341e46d0b3a4c0cca6bfd89d17e94d84616afd3220`.

## Exact canonical tooling

Current `u-dont-existDOTcom/joel-articles`:
- `project-sources/html_islands.py.txt` materialized as `html_islands.py`; local SHA-256 `96c800c9a7c0b1dae642de1139d53651e87b145cb1ae2aefa4075a9affa0b10d`.
- `project-sources/substack_transfer_helper.py.txt` materialized as `substack_transfer_helper.py`; local SHA-256 `322e4738243806570fd01de4389150144f13f959de30d78579b69fb57c9352f4`.
- `project-sources/CONFIRMED-SUBSTACK-HELPER.json`, local SHA-256 as above.

Executed: generator `selftest` PASS; `html_islands inventory/freeze/restore/verify` PASS; helper `init`, `build`, `verify` PASS; manifest identity and payload checks PASS; source editor root mode `substack-editor-root` (not `fragment`); `contenteditable="true"` absent in clipboard payload.

## Owner-approved edits, nothing else

1. **A:** Replace previous Sutta description and mettā effect with Joel's exact two new passages, preserving the Sutta link and his punctuation including `even--love`.
2. **C:** Replace earlier non-prescriptive Oliver caveat paragraph with owner-selected single sentence.
3. **D:** Use owner-approved retreat conclusion and source's existing Plum Village hyperlink; retain original for-profit criticism with original monastery link in its own paragraph. Remove the phrase `I’m not anti-retreat` per approved owner-ending assembly.
4. **E:** Delete the entire overcompletion paragraph with no replacement.
5. **F:** Keep survivor-account introduction, replace former generalized incidence/safety sentences with owner-approved single sentence.
6. **B:** **Unchanged verbatim**. Its previously corrected nibbāna factual dispute is not reopened. No unapproved assistant substitute inserted.

Internally, the string replacement ledger records six exact HTML block operations across five owner-resolved clusters; replacements are outside all five semantic native-object islands. Five original object signatures were preserved byte-for-byte and in their source order: two comment cards, two Substack video-post embeds, and one YouTube. The canonical clipboard converter carries the two comment references and two video-post references as their URL strategies, not as hand-built embed reconstructions. YouTube is carried in rich HTML. No standalone native uploaded videos; **one** ordered clipboard segment, **zero** manual insertion steps.

No Pangram tests were performed. Native-object source fidelity and canonical conversion are checked, but **destination reconstruction is not tested** until a disposable Substack draft is used.

## Delivery

- [Validated helper](deliverables/Goenka-validated-clipboard-20261025.html) (present file in same directory; deployed to user's `Téléchargements`).
- [Edited archival source](Goenka-approved-archival-20261025.html).

Do not label this result a live Substack edit or a whole-article Pangram certification.
