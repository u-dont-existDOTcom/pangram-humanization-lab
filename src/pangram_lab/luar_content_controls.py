from __future__ import annotations

import collections
import hashlib
import json
import random
import re
from pathlib import Path

from .luar_matched_pilot import (
    LuarEmbedder,
    _equal50_folds,
    _read_text,
    _run_condition,
    _whole_folds,
)
from .surface_svm_matched_cv import _hard_control_errors


# Frozen before the control run. This is deliberately a broad English
# closed-class/function-word list rather than a learned vocabulary. The control
# is diagnostic, not a claim that this is a linguistically exhaustive ontology.
_FUNCTION_WORDS = tuple(sorted(set("""
a an the this that these those some any each every either neither no all both
much many few fewer little less enough several another other such
I me my mine myself we us our ours ourselves you your yours yourself yourselves
he him his himself she her hers herself it its itself they them their theirs
themselves one ones who whom whose which what whoever whomever whichever whatever
am is are was were be been being do does did doing have has had having
can could may might must shall should will would ought need dare
and but or nor so yet for if unless because although though while whereas whether
when whenever where wherever why how as than like lest since until till
of to in on at by from with without within into onto upon over under above below
before after between among around through throughout during against toward towards
away off out up down about across along behind beside besides beyond despite except
inside outside near past per via
not only also even just still already again ever never always sometimes often
usually seldom rarely then once here there hence thus therefore however moreover
meanwhile otherwise instead perhaps maybe very too quite rather almost enough
im s m re ve d ll youre youve youll youd hes shes its were theyre theyve theyll
they'd dont doesnt didnt isnt arent wasnt werent havent hasnt hadnt wont wouldnt
cant cannot couldnt shouldnt mustnt mightnt neednt lets thats theres whats whos
here's heres wheres whens whys hows
""".split())))
_FUNCTION_WORD_SET = frozenset(word.lower().replace("’", "'") for word in _FUNCTION_WORDS)
_FUNCTION_WORD_SHA256 = hashlib.sha256(
    ("\n".join(_FUNCTION_WORDS) + "\n").encode("utf-8")
).hexdigest()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _whitespace_tokens(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _whitespace_shape_sha(text: str) -> str:
    shape = "\x1f".join(re.findall(r"\s+", text))
    return _sha(shape)


def _token_multiset_sha(tokens: list[str]) -> str:
    counts = collections.Counter(tokens)
    canonical = json.dumps(sorted(counts.items()), ensure_ascii=False, separators=(",", ":"))
    return _sha(canonical)


def deterministic_block_shuffle(text: str, *, seed: int, block_words: int = 50) -> tuple[str, dict]:
    """Shuffle whitespace-token order within fixed blocks while preserving slots.

    Tokens (including attached punctuation/case) are permuted into the original
    whitespace slots, so the exact token multiset and whitespace pattern are
    unchanged. Keeping 50-token blocks in place limits a whole-document
    truncation confound: lexical material does not migrate arbitrarily across
    distant parts of the document.
    """
    if block_words < 2:
        raise ValueError("block_words must be at least 2")
    tokens = _whitespace_tokens(text)
    shuffled: list[str] = []
    text_sha = _sha(text)
    changed_blocks = 0
    for block_index, start in enumerate(range(0, len(tokens), block_words)):
        block = list(tokens[start : start + block_words])
        if len(block) > 1:
            material = f"{seed}:{text_sha}:{block_index}".encode("utf-8")
            rng_seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
            rng = random.Random(rng_seed)
            order = list(range(len(block)))
            rng.shuffle(order)
            if order == list(range(len(block))) and len(block) > 1:
                order = order[1:] + order[:1]
            transformed = [block[index] for index in order]
            if transformed != block:
                changed_blocks += 1
            block = transformed
        shuffled.extend(block)

    iterator = iter(shuffled)
    output = re.sub(r"\S+", lambda _: next(iterator), text)
    input_tokens = tokens
    output_tokens = _whitespace_tokens(output)
    if collections.Counter(input_tokens) != collections.Counter(output_tokens):
        raise AssertionError("shuffle changed lexical token multiset")
    if _whitespace_shape_sha(text) != _whitespace_shape_sha(output):
        raise AssertionError("shuffle changed whitespace pattern")
    audit = {
        "input_sha256": text_sha,
        "output_sha256": _sha(output),
        "whitespace_token_count": len(tokens),
        "block_words": block_words,
        "block_count": (len(tokens) + block_words - 1) // block_words if tokens else 0,
        "changed_blocks": changed_blocks,
        "token_multiset_sha256": _token_multiset_sha(input_tokens),
        "token_multiset_preserved": True,
        "whitespace_pattern_preserved": True,
    }
    return output, audit


def _normalized_lookup(token: str) -> str:
    letters = re.sub(r"[^A-Za-z'’]", "", token).lower().replace("’", "'")
    return letters.strip("'")


def function_word_mask(text: str) -> tuple[str, dict]:
    """Mask content-bearing alphanumeric material while preserving form.

    Closed-class/function words remain untouched. Other alphabetic/numeric runs
    become `X`, while punctuation and all original whitespace remain in place.
    This is an intentionally severe content-light diagnostic and may be
    out-of-distribution for LUAR; a negative result is therefore not proof that
    style signal is absent.
    """
    retained = 0
    masked = 0
    punctuation_only = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal retained, masked, punctuation_only
        token = match.group(0)
        lookup = _normalized_lookup(token)
        if lookup and lookup in _FUNCTION_WORD_SET:
            retained += 1
            return token
        if re.search(r"[A-Za-z0-9]", token):
            masked += 1
            return re.sub(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*", "X", token)
        punctuation_only += 1
        return token

    output = re.sub(r"\S+", replace, text)
    if _whitespace_shape_sha(text) != _whitespace_shape_sha(output):
        raise AssertionError("function-word mask changed whitespace pattern")
    input_count = len(_whitespace_tokens(text))
    output_count = len(_whitespace_tokens(output))
    if input_count != output_count:
        raise AssertionError("function-word mask changed whitespace-token count")
    audit = {
        "input_sha256": _sha(text),
        "output_sha256": _sha(output),
        "whitespace_token_count": input_count,
        "retained_function_tokens": retained,
        "masked_tokens": masked,
        "punctuation_only_tokens": punctuation_only,
        "whitespace_token_count_preserved": True,
        "whitespace_pattern_preserved": True,
        "function_word_list_sha256": _FUNCTION_WORD_SHA256,
        "function_word_count": len(_FUNCTION_WORDS),
    }
    return output, audit


def _safe(value: object) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "sample")).strip("-") or "sample"


def transform_folds(folds, *, transform_name: str, out_dir: Path, seed: int, block_words: int):
    """Transform fold-local runtime texts and return metadata-only audits."""
    transformed_folds = []
    audits = []
    for fold_index, (held_out_group, train_rows, test_rows) in enumerate(folds, start=1):
        fold_train = []
        fold_test = []
        for role, rows, target_rows in (
            ("train", train_rows, fold_train),
            ("test", test_rows, fold_test),
        ):
            for row_index, row in enumerate(rows, start=1):
                source = _read_text(row)
                if transform_name == "shuffle":
                    output, audit = deterministic_block_shuffle(
                        source, seed=seed, block_words=block_words
                    )
                elif transform_name == "function_mask":
                    output, audit = function_word_mask(source)
                else:
                    raise ValueError(f"unknown transform: {transform_name}")
                target = (
                    out_dir
                    / transform_name
                    / f"fold-{fold_index}"
                    / role
                    / f"{row_index:02d}-{_safe(row.get('sample_id'))}-{audit['output_sha256'][:12]}.txt"
                )
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(output, encoding="utf-8")
                transformed = dict(row)
                transformed["local_text_path"] = str(target)
                transformed["canonical_sha256"] = audit["output_sha256"]
                transformed["word_count"] = len(_whitespace_tokens(output))
                target_rows.append(transformed)
                audits.append(
                    {
                        "fold_index": fold_index,
                        "role": role,
                        "sample_id": row.get("sample_id"),
                        "source_group": row.get("source_group"),
                        "speaker": row.get("speaker"),
                        "transform": transform_name,
                        **audit,
                    }
                )
        transformed_folds.append((held_out_group, fold_train, fold_test))
    return transformed_folds, audits


def run_controls(
    spec_path: Path,
    *,
    matched_manifest_path: Path,
    supplement_manifest_path: Path,
    control_manifest_path: Path,
    working_dir: Path,
    out_path: Path,
) -> dict:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    matched = json.loads(matched_manifest_path.read_text(encoding="utf-8"))
    supplement = json.loads(supplement_manifest_path.read_text(encoding="utf-8"))
    controls = json.loads(control_manifest_path.read_text(encoding="utf-8"))
    if matched.get("errors"):
        raise ValueError(f"matched acquisition errors: {matched['errors']}")
    if supplement.get("errors"):
        raise ValueError(f"supplement acquisition errors: {supplement['errors']}")
    hard_errors, documented_control_exclusions = _hard_control_errors(controls.get("errors", []))
    if hard_errors:
        raise ValueError(f"control acquisition errors: {hard_errors}")

    authors = [str(value) for value in spec["authors"]]
    matched_rows = matched.get("results", [])
    supplement_rows = supplement.get("results", [])
    control_rows = controls.get("results", [])

    baseline_spec = spec["baseline_spec"]
    whole = _whole_folds(baseline_spec, matched_rows, supplement_rows, control_rows)
    equal50 = _equal50_folds(
        baseline_spec,
        matched_rows,
        supplement_rows,
        control_rows,
        working_dir=working_dir / "baseline-equal50",
    )

    shuffle = spec["transforms"]["shuffle"]
    seed = int(shuffle["seed"])
    block_words = int(shuffle["block_words"])
    whole_shuffle, audit_whole_shuffle = transform_folds(
        whole,
        transform_name="shuffle",
        out_dir=working_dir,
        seed=seed,
        block_words=block_words,
    )
    equal_shuffle, audit_equal_shuffle = transform_folds(
        equal50,
        transform_name="shuffle",
        out_dir=working_dir / "equal50",
        seed=seed,
        block_words=block_words,
    )
    whole_mask, audit_whole_mask = transform_folds(
        whole,
        transform_name="function_mask",
        out_dir=working_dir,
        seed=seed,
        block_words=block_words,
    )
    equal_mask, audit_equal_mask = transform_folds(
        equal50,
        transform_name="function_mask",
        out_dir=working_dir / "equal50",
        seed=seed,
        block_words=block_words,
    )

    model = spec["model"]
    embedder = LuarEmbedder(
        model_id=str(model["model_id"]),
        revision=str(model["revision"]),
        max_token_length=int(model["max_token_length"]),
        batch_size=int(model.get("batch_size", 8)),
        device="cpu",
    )
    evaluation = spec["evaluation"]
    iterations = int(evaluation["group_bootstrap_accuracy"]["iterations"])
    base_seed = int(evaluation["group_bootstrap_accuracy"]["seed"])
    condition_folds = {
        "whole_document_block_shuffle": whole_shuffle,
        "equal_50_word_shuffle": equal_shuffle,
        "whole_document_function_mask": whole_mask,
        "equal_50_word_function_mask": equal_mask,
    }
    conditions = {}
    for offset, (name, folds) in enumerate(condition_folds.items()):
        conditions[name] = _run_condition(
            name,
            folds,
            authors=authors,
            embedder=embedder,
            bootstrap_iterations=iterations,
            bootstrap_seed=base_seed + offset,
        )

    audits = audit_whole_shuffle + audit_equal_shuffle + audit_whole_mask + audit_equal_mask
    receipt = {
        "schema_version": 1,
        "pilot_status": "luar-content-controls-diagnostic-not-IER",
        "raw_or_canonical_prose_in_output": False,
        "embeddings_persisted_in_output": False,
        "source_group_leakage": False,
        "authors": authors,
        "model": embedder.metadata(),
        "baseline_result_file": spec["baseline_result_file"],
        "conditions": conditions,
        "transform_summary": {
            "shuffle": {
                "seed": seed,
                "block_words": block_words,
                "exact_whitespace_token_multiset_preserved": True,
                "exact_whitespace_pattern_preserved": True,
                "whole_document_note": "block-local shuffling limits migration of lexical material across distant tokenizer-truncation regions",
            },
            "function_mask": {
                "function_word_list_sha256": _FUNCTION_WORD_SHA256,
                "function_word_count": len(_FUNCTION_WORDS),
                "whitespace_token_count_preserved": True,
                "whitespace_pattern_preserved": True,
                "out_of_distribution_warning": True,
            },
        },
        "transform_audit": audits,
        "documented_control_exclusions": documented_control_exclusions,
        "interpretation_guardrails": spec["interpretation"],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="python -m pangram_lab.luar_content_controls")
    parser.add_argument("spec")
    parser.add_argument("--matched-manifest", required=True)
    parser.add_argument("--supplement-manifest", required=True)
    parser.add_argument("--control-manifest", required=True)
    parser.add_argument("--working-dir", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    try:
        receipt = run_controls(
            Path(args.spec),
            matched_manifest_path=Path(args.matched_manifest),
            supplement_manifest_path=Path(args.supplement_manifest),
            control_manifest_path=Path(args.control_manifest),
            working_dir=Path(args.working_dir),
            out_path=Path(args.out),
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
