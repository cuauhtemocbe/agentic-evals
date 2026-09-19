---
title: Fail-Closed Trivy Pre-Push CVE Gate
status: completed
created: 2026-09-18
updated: 2026-09-18
issue: meta-projects#41
---

# Fail-Closed Trivy Pre-Push CVE Gate

## Objective

Add a `pre-push` git hook that runs Trivy's filesystem vulnerability scanner
and blocks the push if it finds any CRITICAL-severity, fixable CVE — and
also blocks the push if Trivy itself isn't installed. This is agentic-evals'
slice of a fleet-wide rollout (meta-projects issue #41) standardizing a
local, fail-closed CVE gate across repos before code leaves a developer's
machine.

## Context

agentic-evals already has a versioned, opt-in hooks directory: `.githooks/`,
containing `pre-commit` (`make lint` + `make format-check`), activated once
per clone via `make install-hooks` (sets `core.hooksPath` to `.githooks` —
see `README.md`). There is currently no local gate for known CVEs in
dependencies; `/trivy-scan` exists only as an on-demand skill.

The activation mechanism already exists and is already documented, so this
change only adds a new hook file to that directory and widens the existing
`install-hooks` recipe from `chmod +x .githooks/pre-commit` to
`chmod +x .githooks/*` so the new hook is made executable too. No new install
script (the fleet spec's generic `scripts/install-hooks.sh` is deliberately
not created here — same decision as AvocadoDash).

The hook calls the `trivy` CLI directly on the host. Trivy is not a project
dependency, so the hook fails closed — blocks the push — if `trivy` isn't on
`PATH`, rather than silently skipping the scan. The scan covers both Poetry
lockfiles in the tree: `poetry.lock` (root) and
`docs/Modulo 02/Proyecto_02/poetry.lock`.

## Requirements

### Functional Requirements

- [x] A new `.githooks/pre-push` hook runs on `git push` once
      `make install-hooks` has been run (same activation as `pre-commit`).
- [x] The hook checks for `trivy` on `PATH`. If missing, it prints a message
      pointing to `.claude/skills/trivy-scan/setup.md` and exits non-zero,
      blocking the push (fail closed, not skip-if-missing).
- [x] If `trivy` is present, the hook runs
      `trivy fs . --scanners vuln --severity CRITICAL --exit-code 1 --ignore-unfixed --quiet`
      against the repo root.
- [x] A CRITICAL-severity vulnerability with an available fix blocks the push
      (non-zero exit, table output shown); HIGH/MEDIUM findings and unfixed
      CRITICALs do not.
- [x] `make install-hooks` makes every file under `.githooks/` executable
      (`chmod +x .githooks/*`), and its `make help` text mentions the
      pre-push gate.
- [x] `README.md` documents the pre-push gate next to the existing
      `make install-hooks` note: needs `trivy` on `PATH`, fail-closed,
      CRITICAL+fixable only.

### Non-Functional Requirements

- [x] No new activation mechanism: reuses `.githooks/` + `make
      install-hooks`.
- [x] Side-effect-free: the hook only scans and may abort; it makes no
      commits or file changes.
- [x] Local-only: no CI workflow or server-side gate; does not require
      Docker.
- [x] No Engram-related step, file, or reference (fleet spec: out of scope
      permanently).

## Architecture

### Components

- `.githooks/pre-push` (new): bash script, `set -uo pipefail` (deliberately
  not `-e`, since its `if` branches must reach their explicit `exit`
  statements). Two gated steps: `command -v trivy` → exit 1 with a
  setup-doc pointer if absent; then the `trivy fs` invocation above, whose
  failure exits 1.
- `Makefile` `install-hooks` (modified): `chmod +x .githooks/*`, updated
  help text.
- `README.md` (modified): one note about the pre-push gate.

### Data Model

N/A — git-hook tooling only.

### External Dependencies

- [Trivy](https://github.com/aquasecurity/trivy) CLI on the developer's
  `PATH`, installed per `.claude/skills/trivy-scan/setup.md`. Note that
  `.claude/` is a local, gitignored folder in this repo, so that pointer only
  resolves on machines that have the local skills installed.

## User Stories

Tracked at the fleet level in meta-projects issue #41. No repo-local GitHub
issue is created for this slice; this spec is the tracking artifact.

## Testing Strategy

### Unit Tests

N/A — shell hook, no unit-testable code.

### Integration Tests

Manual verification by direct hook invocation, using throwaway manifests in a
temp dir outside the repo (removed afterwards):

- Real repo: hook exits 0 (both lockfiles report 0 vulnerabilities).
- `trivy` missing (`/usr/bin/env -i PATH=/nonexistent /bin/bash
  .githooks/pre-push`): exit 1 with the "trivy not found" message.
- `pyyaml==5.3` (CRITICAL, fixed in 5.4 / 5.3.1): exit 1, table names the
  package and CVE.
- `pycrypto==2.6.1` (CRITICAL/HIGH, no fix) and `requests==2.19.1`
  (HIGH/MEDIUM only): exit 0.
- Fresh repo with the hook and Makefile: `git push` before `make
  install-hooks` is not blocked (hook inactive); after it, a push containing
  the CRITICAL manifest is blocked.

### E2E Tests

N/A — direct hook invocation plus a local `git push` to a throwaway bare
remote is the accepted verification standard.

### Performance Tests

N/A — the real-repo scan took ~0.4 s with the Trivy DB cached; first run on a
machine downloads the DB.

## Boundaries & Constraints

### In Scope

- `.githooks/pre-push`, the `install-hooks` recipe/help text, and the README
  note.

### Out of Scope

- `scripts/install-hooks.sh` or any parallel activation mechanism.
- Changes to `.githooks/pre-commit`, thresholds, or scanners other than
  `vuln`.
- CI-side scanning; auto-installing Trivy.
- CLAUDE.md / `.claude/` (gitignored local copies, not committed).

### Technical Constraints

- Hook must be executable (mode 755) and committed under `.githooks/`.
- Must not assume Docker is running, unlike `pre-commit`.

## Success Criteria

- [x] `.githooks/pre-push` exists, is executable, and matches the fleet-wide
      hook contract exactly.
- [x] Pre-activation scan (`trivy fs . --scanners vuln --severity CRITICAL
      --ignore-unfixed`) is clean: 0 vulnerabilities across both lockfiles.
- [x] All five integration scenarios above behave as specified.
- [x] `make install-hooks` activates the hook alongside `pre-commit`.
- [x] No Engram-related file or reference added.

## Implementation Plan

No separate `-plan.md` — a single fully specified hook script plus a
one-line Makefile change and a README note; nothing to sequence.
