# Branch Protection — recommended GitHub settings

GitHub branch protection rules cannot live in the repo as configuration; they must be configured by a repo admin in **Settings → Branches → Branch protection rules**. This document is the source of truth for what those settings should be, so they can be re-applied if the repo is migrated, forked, or accidentally reset.

One protected branch: **`qa`** — the trunk and release branch. A merge to `qa`
builds the production images and deploys them, so it carries the strictest rules.
(`prod` exists as a future-state release-train branch and should get the same rules
if/when it becomes part of the active deploy flow.)

## Settings to apply to `qa`

In **Settings → Branches → Add branch protection rule**, set the branch name pattern to the target branch, then enable:

### Require a pull request before merging
- ☑ **Require a pull request before merging**
  - ☑ **Require approvals**: minimum **1** review
  - ☑ **Dismiss stale pull request approvals when new commits are pushed**
  - ☐ Require review from Code Owners (no CODEOWNERS file yet — re-evaluate when one is added)

### Require status checks to pass before merging
- ☑ **Require status checks to pass before merging**
- ☑ **Require branches to be up to date before merging**
- Required checks (names match jobs in [`.github/workflows/ci-cd.yaml`](../../.github/workflows/ci-cd.yaml)):
  - `Lint`
  - `Type Check (mypy)`
  - `Security Audit`
  - `Test`
  - `Frontend (Lint, Types, Tests)`

### Other rules
- ☑ **Require conversation resolution before merging**
- ☑ **Do not allow bypassing the above settings** (applies rules to admins too)
- ☐ **Allow force pushes** — leave disabled
- ☐ **Allow deletions** — leave disabled
- ☐ **Require signed commits** — not currently required; revisit if signing keys become standard for the team

## Why these settings

| Setting | Reason |
|---|---|
| Require PR + 1 approval | Catches obvious mistakes; one set of human eyes on every change reaching `qa`. |
| Dismiss stale approvals on new commits | Prevents "approved, then silently changed" bypass. |
| Require status checks | CI catches lint/type/test/security regressions before merge. The required-check list mirrors the job names that block release. |
| Require up-to-date branches | Forces rebases before merge so the CI signal is meaningful against the latest target. |
| Require conversation resolution | Ensures review comments aren't merged-over. |
| Block force-push and deletion | `qa` is shared history — losing commits or rewriting history breaks everyone's clones. |
| Apply to admins ("Do not allow bypassing") | Self-explanatory; the rules are worthless if the most active committers can skip them. |

## Repo-level settings for Dependabot auto-merge

The [`Dependabot auto-merge`](../../.github/workflows/dependabot-automerge.yaml) workflow approves and queues minor/patch dependency bumps once CI is green. For it to actually complete a merge, two repo-level settings (outside branch protection) must be enabled:

- **Settings → General → Pull Requests → ☑ Allow auto-merge** — without this, `gh pr merge --auto` errors.
- **Settings → Actions → General → Workflow permissions → ☑ Allow GitHub Actions to create and approve pull requests** — lets the workflow's auto-approve step satisfy the "Require approvals: 1" rule above. Without it, minor/patch PRs queue but never merge because they sit unapproved.

Majors are intentionally excluded from auto-merge and always need a manual review + approval.

## Verifying the configuration

After applying, the easiest sanity check is to open a draft PR with a deliberately failing test or lint error and confirm GitHub blocks the merge button until the check passes.

To inspect the current configuration via the CLI:

```bash
gh api repos/openshiksha/openshiksha/branches/qa/protection
```

If the command returns `404 Not Found`, protection is not configured on `qa` and this document should be applied.
