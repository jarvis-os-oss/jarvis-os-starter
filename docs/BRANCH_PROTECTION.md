# Branch protection

The `main` branch is the deployable line and must be protected. No direct
commits, changes land only through reviewed pull requests.

## Recommended GitHub settings (Settings -> Branches -> add rule for `main`)

- Require a pull request before merging.
- Require at least 1 approving review.
- Require status checks to pass before merging: select the `ci` workflow
  (`test` job). This makes the secret scan and tests a hard gate.
- Require branches to be up to date before merging.
- Do not allow bypassing the above settings (include administrators).
- Restrict who can push to matching branches (the deploy/maintenance identity only).

## Workflow

1. The developer agent works on a feature branch: `dev/<short-feature-desc>`.
2. It opens a PR against `main` and reports the branch to the maintenance agent.
3. CI runs the secret/PII scan and the test suite on the PR.
4. The maintenance agent reviews, and only then merges to `main` and deploys.

The instance that writes the code must not be the instance that signs off on its
security and deployment. That separation is deliberate.

## One-line reminder for the roles

- Developer agent: build on `dev/*`, open PR, never merge own work, never deploy.
- Maintenance agent: review, merge, deploy. Only holder of production access.
