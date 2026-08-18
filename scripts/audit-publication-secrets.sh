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
git fetch --force --no-tags origin \
  '+refs/heads/*:refs/remotes/origin/*' \
  '+refs/tags/*:refs/tags/*' \
  '+refs/pull/*/head:refs/remotes/pull/*'

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

python3 - "$git_report" "$git_status" "$hosted_report" "$hosted_status" "$fetched_logs" "$unavailable_logs" <<'PY'
import json
import sys
from pathlib import Path

def validate(path_s, status_s, label):
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
    return len(data)

git_findings = validate(sys.argv[1], sys.argv[2], "git")
hosted_findings = validate(sys.argv[3], sys.argv[4], "hosted")
fetched_logs = int(sys.argv[5])
unavailable_logs = int(sys.argv[6])
print(json.dumps({
    "status": "pass" if git_findings == 0 and hosted_findings == 0 else "blocked",
    "git_secret_findings": git_findings,
    "hosted_secret_findings": hosted_findings,
    "actions_logs_scanned": fetched_logs,
    "actions_logs_unavailable_or_expired": unavailable_logs,
}, sort_keys=True))
if git_findings or hosted_findings:
    raise SystemExit(1)
PY
