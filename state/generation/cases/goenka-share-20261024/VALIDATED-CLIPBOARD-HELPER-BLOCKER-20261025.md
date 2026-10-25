# Validated Goenka clipboard helper: source recovery boundary (2026-10-25)

Owner request: “ok well give the updated clipboard helper and btw you should use the VALIDATED one not one you invented”.

## Correct generator and actual readiness

The canonical authoring contract is `joel-articles/docs/SUBSTACK-HELPER-DELIVERY-GATE.md`, with current generator `project-sources/substack_transfer_helper.py.txt`, exact native-object parser `project-sources/html_islands.py.txt`, and `project-sources/CONFIRMED-SUBSTACK-HELPER.json`. These were re-fetched from current GitHub and materialized without source edits in the authorized user's local directory `/tmp/goenka-validated-helper/`.

SHA-256 on local restored exact bytes:
- generator: `322e4738243806570fd01de4389150144f13f959de30d78579b69fb57c9352f4`;
- native-object parser: `96c800c9a7c0b1dae642de1139d53651e87b145cb1ae2aefa4075a9affa0b10d`;
- compatibility profile: `c58bf6928274eb9734194c280a8a5f3b53be50d0e913e7cfb24c23593af05734`.

`python3 substack_transfer_helper.py selftest` completed with PASS; it exercised `init`, `build`, and `verify` against its native-video fixture. This does **not** constitute verification of a Goenka source-bound helper.

## Blocking source issue

Browser connector read the current signed-in Substack editing tab for the Goenka article at `https://ibogaqueen.substack.com/publish/post/169926526`. It provides simplified page text/link/image markup, not the raw `[data-testid="editor"].tiptap.ProseMirror` outerHTML. The currently available published page is rendered HTML, which is **not** authoritative raw editor HTML for native objects. Current GitHub article registry does not register Goenka as an article, and the old, unrelated `Spiritual Bypass Warning` Library sources are not interchangeable with this published Goenka article. A filesystem search found no exact raw Goenka editor HTML snapshot. The previous custom five-patch helper is **unverified and must not be relabeled or reused as the canonical helper**.

The last mandatory input is the exact present source editor outerHTML. If the user supplies it, run `html_islands.py inventory/freeze/restore/verify`, apply only the already authorized five local edits recorded in the case plus owner-final mettā, then execute canonical generator `init/build/verify` and inspect its manifest. Recheck owner status of B before any alteration; the factual nibbāna objection was already resolved. Do not change any original native object. Report destination test separately.

## Safe minimal owner action if computer-control route unavailable

In the existing Substack editor tab, open DevTools Console and save the `document.querySelector('[data-testid="editor"].tiptap.ProseMirror').outerHTML` to a local `.html` file for upload. This is a read-only DOM extraction, not publication. The source must be inspected for the current post identity and exact expected anchors.

**Status:** source-bound build BLOCKED; no validated replacement helper delivered; no article mutation, publication or Pangram call.
