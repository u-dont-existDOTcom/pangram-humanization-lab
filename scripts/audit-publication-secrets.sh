#!/usr/bin/env bash
set -euo pipefail

EXPECTED_REPOSITORY="u-dont-existDOTcom/pangram-humanization-lab"
GITLEAKS_VERSION="8.29.1"
GITLEAKS_SHA256="e4eb209d04e20339d77122a3bdf9cd41351255cfb27ebcb75e85325e04f88924"
GITLEAKS_URL="https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"

repository="${GITHUB_REPOSITORY:-$EXPECTED_REPOSITORY}"
if [[ "$repository" != "$EXPECTED_REPOSITORY" ]]; then
  echo "publication-audit: unexpected repository" >&2
  exit 2
fi
if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "publication-audit: unsupported scanner platform" >&2
  exit 2
fi

umask 077
work="$(mktemp -d /tmp/pangram-publication-audit.XXXXXX)"
trap 'rm -rf -- "$work"' EXIT
mkdir -p "$work/hosted/actions" "$work/hosted/reviews"
chmod 700 "$work" "$work/hosted" "$work/hosted/actions" "$work/hosted/reviews"

# Make every currently reachable branch, tag, and PR head visible to git rev-list/log.
# Keep PR heads in their own remote namespace because actions/checkout may already
# create refs/remotes/pull/<number>/merge for a pull_request run.
git fetch --force --no-tags origin \
  '+refs/heads/*:refs/remotes/origin/*' \
  '+refs/tags/*:refs/tags/*' \
  '+refs/pull/*/head:refs/remotes/pull-heads/*'

git for-each-ref --format='%(refname)' > "$work/hosted/ref-names.txt"
git log --all --format='%H%n%B%n---END-COMMIT---' > "$work/hosted/commit-messages.txt"

archive="$work/gitleaks.tar.gz"
curl --fail --location --silent --show-error "$GITLEAKS_URL" --output "$archive"
printf '%s  %s\n' "$GITLEAKS_SHA256" "$archive" | sha256sum --check --status || {
  echo "publication-audit: gitleaks checksum mismatch" >&2
  exit 2
}
tar -xzf "$archive" -C "$work" --no-same-owner --no-same-permissions gitleaks
chmod 700 "$work/gitleaks"

# GitHub-hosted disclosure surfaces. The repository's prose/test corpus is owner-approved
# for disclosure; this collection exists specifically to detect credential/private-key material.
if command -v gh >/dev/null 2>&1 && [[ -n "${GH_TOKEN:-}" ]]; then
  gh issue list --repo "$repository" --state all --limit 1000 --json number,title,body > "$work/hosted/issues.json"
  gh pr list --repo "$repository" --state all --limit 1000 --json number,title,body > "$work/hosted/pulls.json"
  gh api --method GET --paginate "repos/$repository/issues/comments?per_page=100" > "$work/hosted/issue-comments.json"
  gh api --method GET --paginate "repos/$repository/pulls/comments?per_page=100" > "$work/hosted/review-comments.json"
  gh api --method GET --paginate "repos/$repository/releases?per_page=100" > "$work/hosted/releases.json"

  mapfile -t pr_numbers < <(gh pr list --repo "$repository" --state all --limit 1000 --json number --jq '.[].number')
  for number in "${pr_numbers[@]}"; do
    gh api --method GET --paginate "repos/$repository/pulls/$number/reviews?per_page=100" > "$work/hosted/reviews/pr-$number.json"
  done

  mapfile -t run_ids < <(gh run list --repo "$repository" --limit 1000 --json databaseId --jq '.[].databaseId')
  fetched_logs=0
  unavailable_logs=0
  for run_id in "${run_ids[@]}"; do
    if gh run view "$run_id" --repo "$repository" --log > "$work/hosted/actions/run-$run_id.log" 2>/dev/null; then
      fetched_logs=$((fetched_logs + 1))
    else
      rm -f -- "$work/hosted/actions/run-$run_id.log"
      unavailable_logs=$((unavailable_logs + 1))
    fi
  done
else
  echo "publication-audit: GH_TOKEN/gh required for hosted-surface audit" >&2
  exit 2
fi

git_report="$work/git-report.json"
git_log="$work/git-scan.log"
set +e
"$work/gitleaks" git --no-banner --no-color --redact=100 \
  --report-format=json --report-path="$git_report" --log-opts='--all' "$PWD" \
  > "$git_log" 2>&1
git_status=$?
set -e

hosted_report="$work/hosted-report.json"
hosted_log="$work/hosted-scan.log"
set +e
"$work/gitleaks" dir --no-banner --no-color --redact=100 \
  --report-format=json --report-path="$hosted_report" "$work/hosted" \
  > "$hosted_log" 2>&1
hosted_status=$?
set -e

python3 - "$git_report" "$git_status" "$hosted_report" "$hosted_status" "$fetched_logs" "$unavailable_logs" "$PWD" <<'PY'
import json
import re
import subprocess
import sys
from pathlib import Path

repo = Path(sys.argv[7]).resolve()
FIXTURE_FILES = {
    "tests/regression/test_supervisor_security.py",
    "docs/interactive-supervisor/implementation-plan.md",
    "docs/superpowers/plans/2026-08-12-interactive-supervisor-pause.md",
}
FIXTURE_LITERAL = "PANGRAM-SECRET-FIXTURE-4927"
MEASUREMENT_KEY_LINE = re.compile(
    r'^\s*"(?:measurement_key|first_human_measurement_key)"\s*:\s*"[^"]+"\s*,?\s*$'
)


def historical_line(finding):
    commit = finding.get("Commit")
    file_name = finding.get("File")
    line_number = finding.get("StartLine")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40,64}", commit):
        return None
    if not isinstance(file_name, str) or not file_name or file_name.startswith("/") or ".." in Path(file_name).parts:
        return None
    if not isinstance(line_number, int) or line_number <= 0:
        return None
    result = subprocess.run(
        ["git", "show", f"{commit}:{file_name}"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        return None
    lines = result.stdout.splitlines()
    if line_number > len(lines):
        return None
    return file_name, lines[line_number - 1]


def known_generic_false_positive(finding):
    if finding.get("RuleID") != "generic-api-key":
        return False
    source = historical_line(finding)
    if source is None:
        return False
    file_name, line = source
    if MEASUREMENT_KEY_LINE.fullmatch(line):
        return True
    if file_name in FIXTURE_FILES and FIXTURE_LITERAL in line:
        return True
    return False


def load_and_validate(path_s, status_s, label):
    path = Path(path_s)
    if not path.is_file() or path.is_symlink() or path.stat().st_size == 0:
        raise SystemExit(f"publication-audit: invalid {label} scanner report")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"publication-audit: unreadable {label} scanner report") from exc
    if not isinstance(data, list):
        raise SystemExit(f"publication-audit: malformed {label} scanner report")
    status = int(status_s)
    if status == 0 and data:
        raise SystemExit(f"publication-audit: inconsistent {label} scanner result")
    if status == 1 and not data:
        raise SystemExit(f"publication-audit: inconsistent {label} scanner result")
    if status not in (0, 1):
        raise SystemExit(f"publication-audit: {label} scanner execution failed")
    return data


git_data = load_and_validate(sys.argv[1], sys.argv[2], "git")
hosted_data = load_and_validate(sys.argv[3], sys.argv[4], "hosted")
ignored = [finding for finding in git_data if known_generic_false_positive(finding)]
unexpected_git = [finding for finding in git_data if not known_generic_false_positive(finding)]
fetched_logs = int(sys.argv[5])
unavailable_logs = int(sys.argv[6])

print(json.dumps({
    "status": "pass" if not unexpected_git and not hosted_data else "blocked",
    "git_raw_findings": len(git_data),
    "git_known_false_positives_ignored": len(ignored),
    "git_secret_findings": len(unexpected_git),
    "hosted_secret_findings": len(hosted_data),
    "actions_logs_scanned": fetched_logs,
    "actions_logs_unavailable_or_expired": unavailable_logs,
}, sort_keys=True))
if unexpected_git or hosted_data:
    raise SystemExit(1)
PY
