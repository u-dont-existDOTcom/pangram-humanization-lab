from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import unicodedata
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, Mapping, Sequence

ALGORITHM_VERSION = "pangram-lab-surface-idiolect-v1"
REPORT_SCHEMA_VERSION = 1

_WORD_RE = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
_SENTENCE_RE = re.compile(r"[^.!?]+(?:[.!?]+|$)", re.UNICODE)
_PUNCTUATION = tuple(".,;:!?-—–()[]{}'\"…/")

# A deliberately finite, reviewable English function-word list. It supports a
# content-light channel; it is not a claim to linguistic completeness.
_FUNCTION_WORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further had hadn't has hasn't have haven't having he he'd he'll he's
    her here here's hers herself him himself his how how's i i'd i'll i'm i've
    if in into is isn't it it's its itself just me more most mustn't my myself
    no nor not of off on once only or other ought our ours ourselves out over
    own same shan't she she'd she'll she's should shouldn't so some such than
    that that's the their theirs them themselves then there there's these they
    they'd they'll they're they've this those through to too under until up
    very was wasn't we we'd we'll we're we've were weren't what what's when
    when's where where's which while who who's whom why why's will with won't
    would wouldn't you you'd you'll you're you've your yours yourself yourselves
    """.split()
)

_SENTENCE_BINS = (
    (5, "01-05"),
    (10, "06-10"),
    (20, "11-20"),
    (35, "21-35"),
    (60, "36-60"),
)
_PARAGRAPH_BINS = (
    (25, "001-025"),
    (60, "026-060"),
    (120, "061-120"),
    (240, "121-240"),
)
_WORD_LENGTH_BINS = (
    (2, "01-02"),
    (4, "03-04"),
    (7, "05-07"),
    (11, "08-11"),
    (16, "12-16"),
)


class IdiolectError(ValueError):
    """Raised when an idiolect report cannot be computed safely."""


@dataclass(frozen=True)
class AuthorProfile:
    surface: dict[str, float]
    content_light: dict[str, float]
    sample_count: int
    word_count: int
    corpus_sha256: str
    sample_sha256: tuple[str, ...]


def _normalise_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = (
        text.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    return " ".join(text.lower().split())


def _tokens(text: str) -> list[str]:
    return [token.replace("’", "'").lower() for token in _WORD_RE.findall(text)]


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _corpus_sha256(texts: Sequence[str]) -> tuple[str, tuple[str, ...]]:
    hashes = tuple(sorted(_sha256_text(text) for text in texts))
    payload = json.dumps(hashes, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), hashes


def _unit(counter: Mapping[str, float]) -> dict[str, float]:
    norm = math.sqrt(sum(float(value) ** 2 for value in counter.values()))
    if norm <= 0:
        return {}
    return {key: float(value) / norm for key, value in counter.items() if value}


def _mean_unit(vectors: Sequence[Mapping[str, float]]) -> dict[str, float]:
    if not vectors:
        return {}
    total: Counter[str] = Counter()
    for vector in vectors:
        total.update(vector)
    mean = {key: value / len(vectors) for key, value in total.items()}
    return _unit(mean)


def _cosine(left: Mapping[str, float], right: Mapping[str, float]) -> float:
    if not left or not right:
        return 0.0
    if len(left) > len(right):
        left, right = right, left
    return float(sum(value * right.get(key, 0.0) for key, value in left.items()))


def _bucket(value: int, bins: Sequence[tuple[int, str]], overflow: str) -> str:
    for ceiling, label in bins:
        if value <= ceiling:
            return label
    return overflow


def _surface_features(text: str) -> dict[str, float]:
    normalised = _normalise_text(text)
    tokens = _tokens(normalised)
    counts: Counter[str] = Counter()

    for n in (2, 3, 4):
        for index in range(max(0, len(normalised) - n + 1)):
            gram = normalised[index : index + n]
            if gram.strip():
                counts[f"char{n}:{gram}"] += 1

    for token in tokens:
        counts[f"word1:{token}"] += 1
    for left, right in zip(tokens, tokens[1:]):
        counts[f"word2:{left} {right}"] += 1
    return _unit(counts)


def _content_light_features(text: str) -> dict[str, float]:
    normalised = unicodedata.normalize("NFKC", text)
    tokens = _tokens(normalised)
    counts: Counter[str] = Counter()

    for token in tokens:
        if token in _FUNCTION_WORDS:
            counts[f"function:{token}"] += 1
        counts[
            "word-length:" + _bucket(len(token), _WORD_LENGTH_BINS, "17+")
        ] += 1
        if "'" in token:
            suffix = token[token.rfind("'") :]
            counts[f"contraction:{suffix}"] += 1

    skeleton: list[str] = []
    for token in tokens:
        mark = token if token in _FUNCTION_WORDS else "*"
        if not skeleton or mark != "*" or skeleton[-1] != "*":
            skeleton.append(mark)
    for left, right in zip(skeleton, skeleton[1:]):
        counts[f"syntax-skeleton:{left} {right}"] += 1

    punctuation_text = (
        normalised.replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
    )
    for char in _PUNCTUATION:
        count = punctuation_text.count(char)
        if count:
            counts[f"punctuation:{char}"] += count
    for run in ("...", "?!", "!?", "--", "—"):
        count = punctuation_text.count(run)
        if count:
            counts[f"punctuation-run:{run}"] += count

    sentence_lengths = [
        len(_tokens(match.group(0)))
        for match in _SENTENCE_RE.finditer(normalised)
        if _tokens(match.group(0))
    ]
    for length in sentence_lengths:
        counts[
            "sentence-length:" + _bucket(length, _SENTENCE_BINS, "61+")
        ] += 1

    paragraphs = [
        len(_tokens(paragraph))
        for paragraph in re.split(r"\n\s*\n", normalised)
        if _tokens(paragraph)
    ]
    for length in paragraphs:
        counts[
            "paragraph-length:" + _bucket(length, _PARAGRAPH_BINS, "241+")
        ] += 1

    raw_tokens = _WORD_RE.findall(normalised)
    for token in raw_tokens:
        letters = "".join(char for char in token if char.isalpha())
        if not letters:
            continue
        if letters.isupper() and len(letters) > 1:
            counts["case:all-caps"] += 1
        elif letters[0].isupper():
            counts["case:initial-cap"] += 1
        else:
            counts["case:lower"] += 1

    return _unit(counts)


def _feature_channels(text: str) -> dict[str, dict[str, float]]:
    return {
        "surface": _surface_features(text),
        "content_light": _content_light_features(text),
    }


def build_profile(reference_texts: Sequence[str]) -> AuthorProfile:
    texts = list(reference_texts)
    if not texts:
        raise IdiolectError("at least one reference sample is required")
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise IdiolectError("reference samples must be non-empty UTF-8 text")

    channel_vectors = [_feature_channels(text) for text in texts]
    corpus_hash, sample_hashes = _corpus_sha256(texts)
    return AuthorProfile(
        surface=_mean_unit([vector["surface"] for vector in channel_vectors]),
        content_light=_mean_unit(
            [vector["content_light"] for vector in channel_vectors]
        ),
        sample_count=len(texts),
        word_count=sum(len(_tokens(text)) for text in texts),
        corpus_sha256=corpus_hash,
        sample_sha256=sample_hashes,
    )


def _text_stats(text: str) -> dict[str, float | int]:
    tokens = _tokens(text)
    sentences = [
        len(_tokens(match.group(0)))
        for match in _SENTENCE_RE.finditer(text)
        if _tokens(match.group(0))
    ]
    paragraphs = [
        len(_tokens(paragraph))
        for paragraph in re.split(r"\n\s*\n", text)
        if _tokens(paragraph)
    ]
    punctuation_count = sum(text.count(char) for char in _PUNCTUATION)
    contraction_count = sum("'" in token or "’" in token for token in tokens)
    first_person_count = sum(
        token in {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours"}
        for token in tokens
    )
    return {
        "word_count": len(tokens),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "mean_sentence_words": (
            float(statistics.fmean(sentences)) if sentences else 0.0
        ),
        "mean_paragraph_words": (
            float(statistics.fmean(paragraphs)) if paragraphs else 0.0
        ),
        "mean_word_characters": (
            float(statistics.fmean(len(token) for token in tokens))
            if tokens
            else 0.0
        ),
        "contractions_per_100_words": (
            100.0 * contraction_count / len(tokens) if tokens else 0.0
        ),
        "first_person_per_100_words": (
            100.0 * first_person_count / len(tokens) if tokens else 0.0
        ),
        "punctuation_per_100_words": (
            100.0 * punctuation_count / len(tokens) if tokens else 0.0
        ),
    }


def _channel_report(
    profile_vector: Mapping[str, float],
    original_vector: Mapping[str, float],
    candidate_vector: Mapping[str, float],
) -> dict[str, float | None]:
    original_similarity = _cosine(profile_vector, original_vector)
    candidate_similarity = _cosine(profile_vector, candidate_vector)
    ratio = (
        candidate_similarity / original_similarity
        if original_similarity > 1e-12
        else None
    )
    return {
        "original_profile_similarity": original_similarity,
        "candidate_profile_similarity": candidate_similarity,
        "candidate_minus_original": candidate_similarity - original_similarity,
        "retention_ratio": ratio,
    }


def retention_report(
    reference_texts: Sequence[str],
    original_text: str,
    candidate_text: str,
) -> dict:
    if not isinstance(original_text, str) or not original_text.strip():
        raise IdiolectError("original text must be non-empty")
    if not isinstance(candidate_text, str) or not candidate_text.strip():
        raise IdiolectError("candidate text must be non-empty")

    profile = build_profile(reference_texts)
    original_channels = _feature_channels(original_text)
    candidate_channels = _feature_channels(candidate_text)
    original_tokens = _tokens(original_text)
    candidate_tokens = _tokens(candidate_text)

    channel_reports = {
        "surface": _channel_report(
            profile.surface,
            original_channels["surface"],
            candidate_channels["surface"],
        ),
        "content_light": _channel_report(
            profile.content_light,
            original_channels["content_light"],
            candidate_channels["content_light"],
        ),
    }

    quality_flags: list[str] = []
    if profile.sample_count < 3:
        quality_flags.append("fewer_than_three_reference_samples")
    if profile.word_count < 1000:
        quality_flags.append("reference_corpus_under_1000_words")
    if _sha256_text(original_text) in profile.sample_sha256:
        quality_flags.append("original_hash_present_in_reference_corpus")
    if len(original_tokens) < 50 or len(candidate_tokens) < 50:
        quality_flags.append("short_boundary_under_50_words")

    deltas = [
        float(channel_reports[name]["candidate_minus_original"])
        for name in ("surface", "content_light")
    ]
    if all(delta >= -1e-12 for delta in deltas):
        direction = "not_farther_from_profile_on_measured_channels"
    elif all(delta < 0 for delta in deltas):
        direction = "farther_from_profile_on_both_measured_channels"
    else:
        direction = "mixed_channel_movement"

    original_set = set(original_tokens)
    candidate_set = set(candidate_tokens)
    union = original_set | candidate_set
    lexical_jaccard = (
        len(original_set & candidate_set) / len(union) if union else 1.0
    )

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "report_type": "single_author_retention_proxy",
        "is_closed_set_ier": False,
        "profile": {
            "sample_count": profile.sample_count,
            "word_count": profile.word_count,
            "corpus_sha256": profile.corpus_sha256,
            "sample_sha256": list(profile.sample_sha256),
        },
        "texts": {
            "original_sha256": _sha256_text(original_text),
            "candidate_sha256": _sha256_text(candidate_text),
            "original": _text_stats(original_text),
            "candidate": _text_stats(candidate_text),
        },
        "edit": {
            "token_change_fraction": 1.0
            - SequenceMatcher(
                None, original_tokens, candidate_tokens, autojunk=False
            ).ratio(),
            "length_ratio": len(candidate_tokens) / max(1, len(original_tokens)),
            "lexical_set_jaccard": lexical_jaccard,
            "lexical_set_jaccard_is_not_semantic_similarity": True,
        },
        "profile_similarity": channel_reports,
        "interpretation": {
            "direction": direction,
            "calibrated_pass_threshold": None,
            "instruction": (
                "Compare candidate movement with the original and inspect the "
                "prose. This proxy cannot certify authorship, fidelity, quality, "
                "or human recognition."
            ),
        },
        "quality_flags": quality_flags,
        "privacy": {
            "raw_text_stored_in_report": False,
            "hashes_only_for_source_identity": True,
        },
    }


def _predict(
    profiles: Mapping[str, AuthorProfile],
    text: str,
    channel: str,
) -> str:
    vector = _feature_channels(text)[channel]
    scored = []
    for author, profile in profiles.items():
        profile_vector = getattr(profile, channel)
        scored.append((_cosine(profile_vector, vector), author))
    # Stable, deterministic tie break: highest similarity, then lexical author.
    return min(scored, key=lambda item: (-item[0], item[1]))[1]


def _validate_closed_set(
    profile_texts: Mapping[str, Sequence[str]],
    items: Sequence[Mapping[str, str]],
) -> tuple[dict[str, list[str]], list[dict[str, str]]]:
    profiles: dict[str, list[str]] = {}
    for author, texts in profile_texts.items():
        if not isinstance(author, str) or not author.strip():
            raise IdiolectError("author labels must be non-empty strings")
        if not isinstance(texts, Sequence) or isinstance(texts, (str, bytes)):
            raise IdiolectError(f"profile for {author!r} must be a list of texts")
        profiles[author] = list(texts)
    if len(profiles) < 2:
        raise IdiolectError("closed-set IER requires at least two authors")

    normalised_items: list[dict[str, str]] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise IdiolectError(f"item {index} must be an object")
        author = item.get("author")
        original = item.get("original")
        rewrite = item.get("rewrite")
        item_id = item.get("id", str(index))
        if author not in profiles:
            raise IdiolectError(f"item {index} references unknown author {author!r}")
        if not isinstance(original, str) or not original.strip():
            raise IdiolectError(f"item {index} original must be non-empty")
        if not isinstance(rewrite, str) or not rewrite.strip():
            raise IdiolectError(f"item {index} rewrite must be non-empty")
        normalised_items.append(
            {
                "id": str(item_id),
                "author": str(author),
                "original": original,
                "rewrite": rewrite,
            }
        )
    if not normalised_items:
        raise IdiolectError("closed-set IER requires at least one aligned item")
    return profiles, normalised_items


def closed_set_ier_report(
    profile_texts: Mapping[str, Sequence[str]],
    items: Sequence[Mapping[str, str]],
) -> dict:
    profile_texts, items = _validate_closed_set(profile_texts, items)
    profiles = {
        author: build_profile(texts) for author, texts in profile_texts.items()
    }
    chance = 1.0 / len(profiles)
    channels: dict[str, dict] = {}

    for channel in ("surface", "content_light"):
        baseline_predictions = [
            _predict(profiles, item["original"], channel) for item in items
        ]
        rewrite_predictions = [
            _predict(profiles, item["rewrite"], channel) for item in items
        ]
        baseline_correct = sum(
            predicted == item["author"]
            for predicted, item in zip(baseline_predictions, items)
        )
        rewrite_correct = sum(
            predicted == item["author"]
            for predicted, item in zip(rewrite_predictions, items)
        )
        baseline_accuracy = baseline_correct / len(items)
        rewrite_accuracy = rewrite_correct / len(items)
        channels[channel] = {
            "baseline_accuracy": baseline_accuracy,
            "rewrite_accuracy": rewrite_accuracy,
            "idiolect_erasure_rate_percentage_points": 100.0
            * (baseline_accuracy - rewrite_accuracy),
            "baseline_margin_over_chance_percentage_points": 100.0
            * (baseline_accuracy - chance),
            "baseline_correct": baseline_correct,
            "rewrite_correct": rewrite_correct,
            "item_count": len(items),
        }

    quality_flags: list[str] = []
    if len(profiles) < 5:
        quality_flags.append("fewer_than_five_authors")
    if len(items) < 20:
        quality_flags.append("fewer_than_twenty_evaluation_items")
    if any(profile.sample_count < 3 for profile in profiles.values()):
        quality_flags.append("one_or_more_profiles_under_three_samples")
    if any(profile.word_count < 1000 for profile in profiles.values()):
        quality_flags.append("one_or_more_profiles_under_1000_words")
    for channel, metrics in channels.items():
        if metrics["baseline_accuracy"] <= chance:
            quality_flags.append(f"baseline_not_above_chance:{channel}")

    dataset_identity = {
        "profiles": {
            author: {
                "corpus_sha256": profile.corpus_sha256,
                "sample_count": profile.sample_count,
                "word_count": profile.word_count,
            }
            for author, profile in sorted(profiles.items())
        },
        "items": [
            {
                "id": item["id"],
                "author": item["author"],
                "original_sha256": _sha256_text(item["original"]),
                "rewrite_sha256": _sha256_text(item["rewrite"]),
            }
            for item in items
        ],
    }
    dataset_sha = hashlib.sha256(
        json.dumps(
            dataset_identity, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
    ).hexdigest()

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "algorithm_version": ALGORITHM_VERSION,
        "report_type": "closed_set_idiolect_erasure_rate",
        "is_closed_set_ier": True,
        "instrument_dependent": True,
        "instrument": (
            "nearest-author cosine against equal-sample profile centroids; "
            "standard-library surface and content-light channels"
        ),
        "paper_instrument_equivalent": False,
        "definition": (
            "baseline original attribution accuracy minus rewritten attribution "
            "accuracy, reported in percentage points"
        ),
        "author_count": len(profiles),
        "item_count": len(items),
        "chance_accuracy": chance,
        "dataset_sha256": dataset_sha,
        "channels": channels,
        "quality_flags": quality_flags,
        "interpretation": {
            "calibrated_pass_threshold": None,
            "instruction": (
                "Interpret only when baseline attribution is meaningfully above "
                "chance and the corpus, genre, and held-out design are adequate. "
                "Results are instrument- and corpus-specific."
            ),
        },
        "privacy": {
            "raw_text_stored_in_report": False,
            "hashes_only_for_source_identity": True,
        },
    }


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise IdiolectError(f"text file not found: {path}")
    return path.read_text(encoding="utf-8")


def _profile_paths(
    explicit: Iterable[str] | None,
    profile_dir: str | None,
) -> list[Path]:
    paths = [Path(value).expanduser() for value in (explicit or [])]
    if profile_dir:
        directory = Path(profile_dir).expanduser()
        if not directory.is_dir():
            raise IdiolectError(f"profile directory not found: {directory}")
        paths.extend(sorted(directory.rglob("*.txt")))
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    if not unique:
        raise IdiolectError(
            "supply at least one --profile file or a --profile-dir containing .txt files"
        )
    return unique


def _write_or_print(report: dict, output: str | None) -> None:
    payload = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if output:
        path = Path(output).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")
        print(f"saved -> {path}")
    else:
        print(payload, end="")


def add_cli_parsers(subparsers: argparse._SubParsersAction) -> None:
    retention = subparsers.add_parser(
        "idiolect-retention",
        help="compare an original and candidate against a private author corpus",
    )
    retention.add_argument(
        "--profile",
        action="append",
        default=[],
        help="reference .txt file; repeat for multiple samples",
    )
    retention.add_argument(
        "--profile-dir",
        help="directory recursively containing reference .txt samples",
    )
    retention.add_argument("--original", required=True, help="original text file")
    retention.add_argument("--candidate", required=True, help="candidate text file")
    retention.add_argument("--output", help="write a metadata-only JSON report")

    ier = subparsers.add_parser(
        "idiolect-ier",
        help="compute closed-set attribution loss on an aligned multi-author dataset",
    )
    ier.add_argument(
        "dataset",
        help=(
            "JSON with profiles {author:[texts]} and items "
            "[{id,author,original,rewrite}]"
        ),
    )
    ier.add_argument("--output", help="write a metadata-only JSON report")


def run_cli(args: argparse.Namespace) -> int:
    if args.cmd == "idiolect-retention":
        paths = _profile_paths(args.profile, args.profile_dir)
        report = retention_report(
            [_read_text(path) for path in paths],
            _read_text(Path(args.original).expanduser()),
            _read_text(Path(args.candidate).expanduser()),
        )
        _write_or_print(report, args.output)
        return 0

    if args.cmd == "idiolect-ier":
        dataset_path = Path(args.dataset).expanduser()
        if not dataset_path.is_file():
            raise IdiolectError(f"dataset file not found: {dataset_path}")
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
        if not isinstance(dataset, dict):
            raise IdiolectError("dataset root must be an object")
        report = closed_set_ier_report(
            dataset.get("profiles") or {},
            dataset.get("items") or [],
        )
        _write_or_print(report, args.output)
        return 0

    raise IdiolectError(f"unsupported idiolect command: {args.cmd}")
