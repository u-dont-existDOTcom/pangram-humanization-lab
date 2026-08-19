#!/usr/bin/env bash
set -euo pipefail

OWNER="${OWNER:-u-dont-existDOTcom}"
PUBLIC_REPO="${PUBLIC_REPO:-${OWNER}/pangram-humanization-lab}"
EXECUTOR_REPO="${EXECUTOR_REPO:-${OWNER}/pangram-private-executor}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)-pangram}"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE_DIR="$SCRIPT_DIR/template"
STATE_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/pangram-private-executor"
DEPLOY_KEY="$STATE_DIR/public-lab-deploy-key"
KNOWN_HOSTS="$STATE_DIR/github_known_hosts"
RUNNER_PARENT="$STATE_DIR/actions-runner-service"

# GitHub-maintained runner service installer, pinned to an exact actions/runner commit.
RUNNER_INSTALLER_COMMIT="258d6c857db3519913f7deb6004b60172f8043ae"
RUNNER_INSTALLER_URL="https://raw.githubusercontent.com/actions/runner/${RUNNER_INSTALLER_COMMIT}/scripts/create-latest-svc.sh"

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if [[ ${EUID:-$(id -u)} -eq 0 ]]; then
  fail "run this bootstrap as your normal user, not root; it will use sudo only for the runner service"
fi

for cmd in git gh curl ssh-keygen python3; do
  command -v "$cmd" >/dev/null 2>&1 || fail "$cmd is required"
done

if ! command -v jq >/dev/null 2>&1; then
  printf 'jq is required by GitHub\'s official runner installer; installing it.\n'
  sudo apt-get update
  sudo apt-get install -y jq
fi

gh auth status >/dev/null 2>&1 || fail "GitHub CLI is not authenticated; run gh auth login first"
LOGIN="$(gh api user --jq .login)"
[[ "$LOGIN" == "$OWNER" ]] || fail "gh is authenticated as $LOGIN, expected $OWNER"
[[ -d "$TEMPLATE_DIR" ]] || fail "template directory missing: $TEMPLATE_DIR"
[[ -n "${PANGRAM_API_KEY:-}" ]] || fail "PANGRAM_API_KEY is not exported in this shell"

printf '=== 1/5 Private executor repository ===\n'
if ! gh repo view "$EXECUTOR_REPO" >/dev/null 2>&1; then
  gh repo create "$EXECUTOR_REPO" \
    --private \
    --description "Private self-hosted execution envelope for Pangram 4 paid batches"
fi
VISIBILITY="$(gh repo view "$EXECUTOR_REPO" --json visibility --jq .visibility)"
[[ "$VISIBILITY" == "PRIVATE" ]] || fail "$EXECUTOR_REPO must remain private (current: $VISIBILITY)"

TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

gh repo clone "$EXECUTOR_REPO" "$TMP/executor" >/dev/null 2>&1 || fail "could not clone $EXECUTOR_REPO"
git -C "$TMP/executor" checkout -B main >/dev/null 2>&1
cp -a "$TEMPLATE_DIR/." "$TMP/executor/"
git -C "$TMP/executor" config user.name "u-dont-exist.com"
git -C "$TMP/executor" config user.email "joel@loveyhuasca.info"
git -C "$TMP/executor" add -A
if ! git -C "$TMP/executor" diff --cached --quiet; then
  git -C "$TMP/executor" commit -m "Install Pangram private executor envelope" >/dev/null
  git -C "$TMP/executor" push -u origin main
else
  printf 'Private executor template already current.\n'
fi

printf '=== 2/5 Pangram secret ===\n'
# gh reads the value from stdin and encrypts it locally; the key is never printed.
printf '%s' "$PANGRAM_API_KEY" | gh secret set PANGRAM_API_KEY --repo "$EXECUTOR_REPO"
gh secret list --repo "$EXECUTOR_REPO" --json name --jq '.[].name' | grep -Fxq PANGRAM_API_KEY \
  || fail "PANGRAM_API_KEY secret was not registered"

printf '=== 3/5 Dedicated public-lab deploy key ===\n'
install -d -m 700 "$STATE_DIR"
if [[ ! -f "$DEPLOY_KEY" ]]; then
  ssh-keygen -q -t ed25519 -N '' \
    -C "pangram-private-executor@$(hostname)" \
    -f "$DEPLOY_KEY"
fi
chmod 600 "$DEPLOY_KEY"
chmod 644 "$DEPLOY_KEY.pub"
PUBKEY="$(cat "$DEPLOY_KEY.pub")"

if ! gh api "repos/$PUBLIC_REPO/keys" --paginate --jq '.[].key' | grep -Fxq "$PUBKEY"; then
  gh api --method POST "repos/$PUBLIC_REPO/keys" \
    -f title="pangram-private-executor-$(hostname)" \
    -f key="$PUBKEY" \
    -F read_only=false >/dev/null
fi

# GitHub's currently published Ed25519 host key; pin it rather than trusting ssh-keyscan.
cat > "$KNOWN_HOSTS" <<'EOF'
github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl
EOF
chmod 600 "$KNOWN_HOSTS"

GIT_SSH_COMMAND="ssh -i $DEPLOY_KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$KNOWN_HOSTS -o StrictHostKeyChecking=yes" \
  git ls-remote "git@github.com:${PUBLIC_REPO}.git" HEAD >/dev/null \
  || fail "dedicated deploy key could not authenticate to $PUBLIC_REPO"

printf '=== 4/5 Repository-level self-hosted runner ===\n'
mkdir -p "$RUNNER_PARENT"
if [[ ! -f "$RUNNER_PARENT/runner/.runner" ]]; then
  [[ ! -e "$RUNNER_PARENT/runner" ]] || fail "partial runner directory exists at $RUNNER_PARENT/runner; inspect/remove it before rerunning"
  INSTALLER="$RUNNER_PARENT/create-latest-svc.sh"
  curl -fsSL --retry 3 --retry-all-errors "$RUNNER_INSTALLER_URL" -o "$INSTALLER"
  chmod 700 "$INSTALLER"
  (
    cd "$RUNNER_PARENT"
    # GitHub's official installer uses this token only to obtain the short-lived runner registration token.
    RUNNER_CFG_PAT="$(gh auth token)" \
      bash "$INSTALLER" \
        -s "$EXECUTOR_REPO" \
        -n "$RUNNER_NAME" \
        -u "$(id -un)" \
        -l pangram \
        -f
  )
else
  printf 'Runner is already configured locally; ensuring its service is started.\n'
  (cd "$RUNNER_PARENT/runner" && sudo ./svc.sh start)
fi

# GitHub recommends excluding the runner service from needrestart on Debian-family systems.
if command -v needrestart >/dev/null 2>&1 || [[ -d /etc/needrestart ]]; then
  printf '%s\n' '$nrconf{override_rc}{qr(^actions\.runner\..+\.service$)} = 0;' \
    | sudo tee /etc/needrestart/conf.d/actions_runner_services.conf >/dev/null
fi

printf '=== 5/5 Readback ===\n'
RUNNER_JSON="$(gh api "repos/$EXECUTOR_REPO/actions/runners" \
  --jq ".runners[] | select(.name == \"$RUNNER_NAME\") | {name,status,busy,labels:[.labels[].name]}")"
[[ -n "$RUNNER_JSON" ]] || fail "runner registration was not visible in GitHub readback"
printf '%s\n' "$RUNNER_JSON"

printf '\nBootstrap complete.\n'
printf 'Private executor: https://github.com/%s\n' "$EXECUTOR_REPO"
printf 'Runner name: %s\n' "$RUNNER_NAME"
printf 'Routine Pangram work can now be triggered by adding validated requests to the private repo; no terminal Pangram command should be required.\n'
