---
size: small
modified_date: 2026-05-18
implemented_git_tag: specs/documentation/spec-frontmatter/implemented
---

# Spec Frontmatter Convention

**Goal**: Every file in `specs/` carries YAML frontmatter with traceability metadata so developers and LLMs can quickly assess a spec's relevance and implementation status.

**Why**: Specs are living documents. After implementation, a spec may be refined, or the codebase may evolve in ways that invalidate its assumptions. Without traceability metadata, there is no quick signal about whether a spec is current, implemented, or stale. By embedding a modification date and an implementation tag directly in the frontmatter, anyone reading a spec gets immediate context without running git commands or opening external tools.

## Current State

Spec files in `specs/` have inconsistent or no YAML frontmatter. Some files have a `size` field, some have `status` or `area`, and some have none. There is no mechanism to track:
- When a spec was last meaningfully changed
- Whether or when it has been implemented

This makes it hard for developers and LLMs to assess a spec's relevance at a glance.

## Target State

Every spec file has a standardized frontmatter block:

```yaml
---
modified_date: 2026-05-16
implemented_git_tag: specs/features/xmp-metadata/implemented
size: medium
---
```

| Field | Required | Description |
|---|---|---|
| `modified_date` | Yes | Date (`YYYY-MM-DD`) of last significant change. Set to creation date on first write. |
| `implemented_git_tag` | No | Git tag name pointing to the implementation commit. **Presence of this field means the spec is implemented.** Omitted for unimplemented specs. |

**Significant modification** = changes to requirements, acceptance criteria, decisions/rationale, or section structure. Factual corrections and typo fixes are also significant (the date should reflect the true last touch). Feature creep or extensions after implementation are **not** allowed — create a new spec instead.

**Tag naming convention**: `specs/<relative-path>/implemented`
- Example: `specs/features/xmp-metadata.md` → `specs/features/xmp-metadata/implemented`

**Tag lifecycle**:
| Event | Action |
|---|---|
| Spec created | Set `modified_date` to today |
| Significant modification | Update `modified_date` |
| Spec implemented | Set `implemented_git_tag`, run `git tag <tag> HEAD` |
| Implementation rework (bugfix, correction) | Move tag: `git tag -f <tag> HEAD`. Spec text stays frozen. |
| Extension needed | Create a new spec. Do not modify the implemented one. |

**Multiple specs in one commit**: Each spec gets its own `modified_date` and tag, all pointing to the same HEAD. Tags are independent refs — no conflict.

## Technical Considerations

- `modified_date` is a plain date string — no git dependency to read it
- `implemented_git_tag` is resolved via `git rev-list -1 <tag>` to find the commit
- Lightweight tags are used (no annotation overhead). They can be force-moved (`git tag -f`) when implementation is reworked
- Tags are local by default — implementers should push with `git push origin <tag>` if the tag needs to be shared
- Existing frontmatter fields (`size`, `status`, `area`, `depends-on`) are preserved alongside the new fields
- The convention is documented in `CONTRIBUTING.md` so all contributors and agents follow it
