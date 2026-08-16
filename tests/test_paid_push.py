import hashlib
import json
from pathlib import Path

import pytest

from scripts.validate_paid_dispatch import PAID_RUN_CONFIRMATION
from scripts.validate_paid_push import (
    PAID_REQUEST_FORMAT,
    PAID_TRIGGER_FORMAT,
    PaidPushValidationError,
    validate_paid_push,
    write_github_output,
)


def _write_spec(root: Path, *, experiment_id: str = "verified-batch") -> tuple[Path, bytes]:
    path = root / "experiments" / "batch.json"
    path.parent.mkdir(parents=True)
    raw = json.dumps(
        {
            "format": "pangram-fixed-batch-v1",
            "experiment_id": experiment_id,
            "audit_id": "audit-1",
            "variants": [
                {
                    "id": "A",
                    "section_id": "opening",
                    "text": "Exact reader-visible text.",
                }
            ],
        },
        sort_keys=True,
    ).encode()
    path.write_bytes(raw)
    return path, raw


def _write_request(
    root: Path,
    raw_spec: bytes,
    *,
    request_id: str = "verified-batch",
    spec_path: str = "experiments/batch.json",
    spec_sha256: str | None = None,
) -> Path:
    path = root / "requests" / "pangram" / f"{request_id}.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "format": PAID_REQUEST_FORMAT,
                "request_id": request_id,
                "spec_path": spec_path,
                "spec_sha256": spec_sha256 or hashlib.sha256(raw_spec).hexdigest(),
                "confirmation": PAID_RUN_CONFIRMATION,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _write_trigger(
    root: Path,
    request: Path,
    *,
    request_id: str = "verified-batch",
    request_sha256: str | None = None,
) -> Path:
    path = root / "triggers" / "pangram" / f"{request_id}.json"
    path.parent.mkdir(parents=True)
    request_relative = request.relative_to(root).as_posix()
    path.write_text(
        json.dumps(
            {
                "format": PAID_TRIGGER_FORMAT,
                "request_id": request_id,
                "request_path": request_relative,
                "request_sha256": request_sha256
                or hashlib.sha256(request.read_bytes()).hexdigest(),
                "confirmation": PAID_RUN_CONFIRMATION,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _valid_change_set(root: Path) -> list[tuple[str, str]]:
    _, raw = _write_spec(root)
    request = _write_request(root, raw)
    return [
        ("A", "experiments/batch.json"),
        ("A", request.relative_to(root).as_posix()),
    ]


def _registered_trigger_change_set(root: Path) -> list[tuple[str, str]]:
    _, raw = _write_spec(root)
    request = _write_request(root, raw)
    trigger = _write_trigger(root, request)
    return [("A", trigger.relative_to(root).as_posix())]


def test_code_only_push_is_free_and_skips_paid_runner(tmp_path: Path) -> None:
    result = validate_paid_push(
        tmp_path,
        changes=[("M", "scripts/run_fixed_batch.py"), ("M", "state/CURRENT-STATE.md")],
    )
    assert result == {"paid_request": False}


def test_exact_added_request_and_spec_authorize_one_automatic_run(tmp_path: Path) -> None:
    result = validate_paid_push(tmp_path, changes=_valid_change_set(tmp_path))
    assert result == {
        "paid_request": True,
        "spec_path": "experiments/batch.json",
        "result_path": "state/experiments/verified-batch-results.json",
    }


def test_paid_request_must_be_immutable_and_added(tmp_path: Path) -> None:
    changes = _valid_change_set(tmp_path)
    changes[1] = ("M", changes[1][1])
    with pytest.raises(PaidPushValidationError, match="added|immutable"):
        validate_paid_push(tmp_path, changes=changes)


def test_paid_request_rejects_any_bundled_third_change(tmp_path: Path) -> None:
    changes = _valid_change_set(tmp_path)
    changes.append(("M", "scripts/run_fixed_batch.py"))
    with pytest.raises(PaidPushValidationError, match="exactly|bundled"):
        validate_paid_push(tmp_path, changes=changes)


def test_paid_request_requires_spec_added_in_same_push(tmp_path: Path) -> None:
    changes = _valid_change_set(tmp_path)
    changes = [changes[1]]
    with pytest.raises(PaidPushValidationError, match="spec|same push"):
        validate_paid_push(tmp_path, changes=changes)


def test_paid_request_binds_exact_spec_bytes(tmp_path: Path) -> None:
    changes = _valid_change_set(tmp_path)
    request = tmp_path / changes[1][1]
    obj = json.loads(request.read_text(encoding="utf-8"))
    obj["spec_sha256"] = "0" * 64
    request.write_text(json.dumps(obj), encoding="utf-8")
    with pytest.raises(PaidPushValidationError, match="sha256|digest"):
        validate_paid_push(tmp_path, changes=changes)


def test_request_identity_matches_filename_and_experiment(tmp_path: Path) -> None:
    _, raw = _write_spec(tmp_path)
    request = _write_request(tmp_path, raw, request_id="different-request")
    changes = [
        ("A", "experiments/batch.json"),
        ("A", request.relative_to(tmp_path).as_posix()),
    ]
    with pytest.raises(PaidPushValidationError, match="request_id|experiment"):
        validate_paid_push(tmp_path, changes=changes)


def test_symlinked_request_or_spec_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "actual"
    _, raw = _write_spec(target)
    request = _write_request(target, raw)
    (tmp_path / "experiments").symlink_to(target / "experiments", target_is_directory=True)
    (tmp_path / "requests").symlink_to(target / "requests", target_is_directory=True)
    changes = [
        ("A", "experiments/batch.json"),
        ("A", request.relative_to(target).as_posix()),
    ]
    with pytest.raises(PaidPushValidationError, match="symlink"):
        validate_paid_push(tmp_path, changes=changes)


def test_registered_trigger_authorizes_existing_hash_bound_request_once(tmp_path: Path) -> None:
    result = validate_paid_push(tmp_path, changes=_registered_trigger_change_set(tmp_path))
    assert result == {
        "paid_request": True,
        "spec_path": "experiments/batch.json",
        "result_path": "state/experiments/verified-batch-results.json",
    }


def test_registered_trigger_must_be_new_and_unbundled(tmp_path: Path) -> None:
    changes = _registered_trigger_change_set(tmp_path)
    with pytest.raises(PaidPushValidationError, match="added|immutable"):
        validate_paid_push(tmp_path, changes=[("M", changes[0][1])])
    with pytest.raises(PaidPushValidationError, match="exactly|bundled"):
        validate_paid_push(
            tmp_path,
            changes=changes + [("M", "scripts/run_fixed_batch.py")],
        )


def test_registered_trigger_binds_exact_existing_request_bytes(tmp_path: Path) -> None:
    _, raw = _write_spec(tmp_path)
    request = _write_request(tmp_path, raw)
    trigger = _write_trigger(tmp_path, request, request_sha256="0" * 64)
    with pytest.raises(PaidPushValidationError, match="request_sha256|digest"):
        validate_paid_push(
            tmp_path,
            changes=[("A", trigger.relative_to(tmp_path).as_posix())],
        )


def test_registered_trigger_identity_and_request_path_are_bound(tmp_path: Path) -> None:
    _, raw = _write_spec(tmp_path)
    request = _write_request(tmp_path, raw)
    trigger = _write_trigger(tmp_path, request, request_id="other-id")
    with pytest.raises(PaidPushValidationError, match="request_id|filename|path"):
        validate_paid_push(
            tmp_path,
            changes=[("A", trigger.relative_to(tmp_path).as_posix())],
        )


def test_registered_trigger_rejects_when_result_already_exists(tmp_path: Path) -> None:
    changes = _registered_trigger_change_set(tmp_path)
    result = tmp_path / "state" / "experiments" / "verified-batch-results.json"
    result.parent.mkdir(parents=True)
    result.write_text("{}\n", encoding="utf-8")
    with pytest.raises(PaidPushValidationError, match="result|already"):
        validate_paid_push(tmp_path, changes=changes)


def test_registered_trigger_rejects_missing_registered_request(tmp_path: Path) -> None:
    _, raw = _write_spec(tmp_path)
    request = _write_request(tmp_path, raw)
    trigger = _write_trigger(tmp_path, request)
    request.unlink()
    with pytest.raises(PaidPushValidationError, match="request|existing"):
        validate_paid_push(
            tmp_path,
            changes=[("A", trigger.relative_to(tmp_path).as_posix())],
        )


def test_github_output_exposes_only_gate_and_validated_paths(tmp_path: Path) -> None:
    result = validate_paid_push(tmp_path, changes=_valid_change_set(tmp_path))
    output = tmp_path / "github-output"
    write_github_output(output, result)
    assert output.read_text(encoding="utf-8").splitlines() == [
        "paid_request=true",
        "spec_path=experiments/batch.json",
        "result_path=state/experiments/verified-batch-results.json",
    ]
