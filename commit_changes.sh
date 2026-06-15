#!/bin/zsh
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./commit_changes.sh "base commit message" [feature-branch]

Examples:
  ./commit_changes.sh "chore(repo): update workflow script" tgusain/add-safe-commit-script
  ./commit_changes.sh "feat(eval): add golden task runner"

Behavior:
  - Detects the remote default branch instead of assuming main or master.
  - Refuses to commit directly to the default branch.
  - Creates or uses a tgusain/* feature branch.
  - Commits each changed file individually.
  - Pushes the feature branch.
  - Opens a pull request.
  - Squash-merges the pull request.
  - Fetches and fast-forwards the local default branch.

Requires:
  - Git remote named origin.
  - GitHub CLI auth, or a GitHub token available from git credential fill.
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

run() {
  echo "+ $*"
  "$@"
}

if [[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

BASE_MESSAGE="$1"
REQUESTED_BRANCH="${2:-}"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

REMOTE="origin"
REMOTE_URL="$(git remote get-url "$REMOTE")"
DEFAULT_BRANCH="$(git remote show "$REMOTE" | sed -n 's/.*HEAD branch: //p')"
[[ -n "$DEFAULT_BRANCH" ]] || die "Unable to detect remote default branch."

CURRENT_BRANCH="$(git branch --show-current)"
[[ -n "$CURRENT_BRANCH" ]] || die "Detached HEAD is not supported."

run git fetch "$REMOTE" --prune

if [[ "$CURRENT_BRANCH" == "$DEFAULT_BRANCH" ]]; then
  if [[ -z "$REQUESTED_BRANCH" ]]; then
    die "Currently on $DEFAULT_BRANCH. Provide a feature branch, for example: tgusain/my-feature"
  fi
  [[ "$REQUESTED_BRANCH" != "$DEFAULT_BRANCH" ]] || die "Feature branch cannot be the default branch."
  run git merge --ff-only "$REMOTE/$DEFAULT_BRANCH"
  if git show-ref --verify --quiet "refs/heads/$REQUESTED_BRANCH"; then
    run git switch "$REQUESTED_BRANCH"
  else
    run git switch -c "$REQUESTED_BRANCH"
  fi
elif [[ -n "$REQUESTED_BRANCH" && "$REQUESTED_BRANCH" != "$CURRENT_BRANCH" ]]; then
  die "Already on $CURRENT_BRANCH. Refusing to switch to $REQUESTED_BRANCH with local changes possible."
fi

FEATURE_BRANCH="$(git branch --show-current)"
[[ "$FEATURE_BRANCH" != "$DEFAULT_BRANCH" ]] || die "Refusing to commit directly to $DEFAULT_BRANCH."
[[ "$FEATURE_BRANCH" == tgusain/* ]] || die "Feature branch must use tgusain/ prefix."

CHANGED_FILES=("${(@f)$(git ls-files -m -o --exclude-standard)}")
if [[ ${#CHANGED_FILES[@]} -eq 0 ]]; then
  echo "No changed files to commit."
  exit 0
fi

for file in "${CHANGED_FILES[@]}"; do
  [[ -f "$file" ]] || continue
  run git add "$file"
  run git commit -m "$BASE_MESSAGE: ${file##*/}"
done

run git fetch "$REMOTE" --prune
run git rebase "$REMOTE/$DEFAULT_BRANCH"
run git push -u "$REMOTE" "$FEATURE_BRANCH"

OWNER_REPO="$(echo "$REMOTE_URL" | sed -E 's#^git@github.com:##; s#^https://github.com/##; s#\.git$##')"
[[ "$OWNER_REPO" == */* ]] || die "Unable to parse GitHub owner/repo from remote URL: $REMOTE_URL"

PR_TITLE="$BASE_MESSAGE"
PR_BODY="## Summary
- Committed changed files individually from $FEATURE_BRANCH.

## Testing
- Not run by commit_changes.sh.

## Merge
- Script-created PR from $FEATURE_BRANCH to $DEFAULT_BRANCH."

if command -v gh >/dev/null 2>&1; then
  PR_URL="$(gh pr create --base "$DEFAULT_BRANCH" --head "$FEATURE_BRANCH" --title "$PR_TITLE" --body "$PR_BODY")"
  echo "Created PR: $PR_URL"
  run gh pr merge "$PR_URL" --squash --delete-branch=false
else
  CREDENTIAL_OUTPUT="$(printf 'protocol=https\nhost=github.com\n\n' | git credential fill)"
  TOKEN="$(echo "$CREDENTIAL_OUTPUT" | sed -n 's/^password=//p')"
  [[ -n "$TOKEN" ]] || die "GitHub CLI is unavailable and no token was found from git credential fill."

  PR_CREATE_PAYLOAD="$(PR_TITLE="$PR_TITLE" FEATURE_BRANCH="$FEATURE_BRANCH" DEFAULT_BRANCH="$DEFAULT_BRANCH" PR_BODY="$PR_BODY" python3 -c 'import json, os; print(json.dumps({"title": os.environ["PR_TITLE"], "head": os.environ["FEATURE_BRANCH"], "base": os.environ["DEFAULT_BRANCH"], "body": os.environ["PR_BODY"]}))')"
  PR_RESPONSE="$(curl -sS -X POST "https://api.github.com/repos/$OWNER_REPO/pulls" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -d "$PR_CREATE_PAYLOAD")"
  PR_NUMBER="$(echo "$PR_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("number", ""))')"
  PR_URL="$(echo "$PR_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("html_url", ""))')"
  [[ -n "$PR_NUMBER" && -n "$PR_URL" ]] || die "Unable to create PR: $PR_RESPONSE"
  echo "Created PR: $PR_URL"

  PR_MERGE_PAYLOAD="$(PR_TITLE="$PR_TITLE" python3 -c 'import json, os; print(json.dumps({"commit_title": os.environ["PR_TITLE"], "commit_message": "", "merge_method": "squash"}))')"
  MERGE_RESPONSE="$(curl -sS -X PUT "https://api.github.com/repos/$OWNER_REPO/pulls/$PR_NUMBER/merge" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    -d "$PR_MERGE_PAYLOAD")"
  MERGED="$(echo "$MERGE_RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("merged", False))')"
  [[ "$MERGED" == "True" ]] || die "Unable to merge PR: $MERGE_RESPONSE"
fi

run git fetch "$REMOTE" --prune
run git switch "$DEFAULT_BRANCH"
run git merge --ff-only "$REMOTE/$DEFAULT_BRANCH"

echo "Done. $DEFAULT_BRANCH is synced with $REMOTE/$DEFAULT_BRANCH."
