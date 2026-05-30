#!/usr/bin/env bash
# setup-github-org.sh — bootstrap GitHub org, repo, and branch protection
# Usage: GH_TOKEN=<token> ORG_NAME=<org> REPO_NAME=<repo> bash setup-github-org.sh
set -euo pipefail

: "${GH_TOKEN:?GH_TOKEN required}"
: "${ORG_NAME:?ORG_NAME required}"
: "${REPO_NAME:=${ORG_NAME}-platform}"

export GH_TOKEN

echo "==> Authenticating..."
echo "$GH_TOKEN" | gh auth login --with-token

echo "==> Checking org: $ORG_NAME"
if gh api "orgs/$ORG_NAME" &>/dev/null; then
  echo "    Org exists, continuing."
else
  echo "    ERROR: org '$ORG_NAME' not found or not accessible."
  echo "    Create it at https://github.com/organizations/new then re-run."
  exit 1
fi

echo "==> Creating repo: $ORG_NAME/$REPO_NAME"
if gh api "repos/$ORG_NAME/$REPO_NAME" &>/dev/null; then
  echo "    Repo already exists."
else
  gh repo create "$ORG_NAME/$REPO_NAME" \
    --public \
    --description "Main platform repository" \
    --gitignore Node \
    --license MIT
fi

echo "==> Cloning and pushing templates..."
TMPDIR=$(mktemp -d)
git clone "https://github.com/$ORG_NAME/$REPO_NAME.git" "$TMPDIR/repo"
cd "$TMPDIR/repo"

# Copy .github templates from this script's directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cp -r "$SCRIPT_DIR/.github" .

git add -A
git diff --cached --quiet || git commit -m "ci: add PR templates, issue templates, and CI/CD workflows

Co-Authored-By: Paperclip <noreply@paperclip.ing>"
git push origin main

echo "==> Setting branch protection on main..."
gh api "repos/$ORG_NAME/$REPO_NAME/branches/main/protection" \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["test"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  2>/dev/null || echo "    Note: branch protection requires org plan or public repo — skipping if free tier."

echo "==> Done."
echo "    Repo: https://github.com/$ORG_NAME/$REPO_NAME"
echo "    Actions: https://github.com/$ORG_NAME/$REPO_NAME/actions"
echo ""
echo "Next steps:"
echo "  1. Go to repo Settings > Environments > Add 'production'"
echo "  2. Add deploy secrets (VERCEL_TOKEN, RAILWAY_TOKEN, etc.) to production env"
echo "  3. Push a commit to main to trigger the deploy workflow"

cd -
rm -rf "$TMPDIR"
