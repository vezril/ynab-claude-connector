## Context

The `ynab-integration` capability (Features 3–4) exposes read-only YNAB tools via an async `httpx` client with typed models, pure parsers, a typed error taxonomy, and a stateless server factory — 62 tests at 100% coverage, ruff/mypy strict across Python 3.11–3.13. Two facts drive this change, both verified against the raw live OpenAPI spec (`https://api.ynab.com/papi/open_api_spec.yaml`, base `https://api.ynab.com/v1`):

1. The API serves the budget/plan endpoints under **`/plans`** (YNAB rebranded "Budgets" → "Plans"); there are **no `/budgets` paths** in the current spec. Our existing tools call `/budgets/...`, which is off-contract (undetected because tests assert our own mocked paths).
2. The **Plans category** has three endpoints: `GET /plans` (list; `PlanSummaryResponse`), `GET /plans/{plan_id}` (full export; `PlanDetailResponse`; supports `last_knowledge_of_server`), and `GET /plans/{plan_id}/settings` (`PlanSettingsResponse`). The `plan_id` path accepts the aliases `"last-used"` and `"default"`.

Per the chosen direction: adopt **plan** terminology throughout (a breaking tool rename, acceptable pre-1.0) and return a **curated summary** from the single-plan endpoint rather than the full export.

## Goals / Non-Goals

**Goals:**
- Correct all existing YNAB request paths to `/plans/...` and rename tools/models to plan terminology.
- Add `get_plan` (curated summary) and `get_plan_settings`, completing the Plans category.
- Preserve the established FP boundaries, full type hints, the 90% coverage floor, and ruff/mypy green. No new dependencies.

**Non-Goals:**
- No full-export dump from `get_plan` (size/limits); no delta sync (`last_knowledge_of_server`); no write operations; no other categories (payees, months, scheduled transactions).
- No backward-compatible aliases for the old `list_budgets`/`budget_id` names (clean rename pre-1.0).

## Decisions

### Decision 1: Adopt plan terminology and `/plans` paths (the breaking rename + correctness fix)
**Choice**: Rename `Budget`→`Plan`, `parse_budgets`→`parse_plans`, `list_budgets`→`list_plans`, and the `budget_id` arg → `plan_id` on the account/category/transaction tools and client methods. Change every request path `/budgets/...` → `/plans/...`.
**Why**: The documented API is `/plans`; building against an undocumented legacy alias is fragile. Matching YNAB's current terminology keeps tool names intuitive. Pre-1.0 makes the rename low-cost.
**Alternatives**: Keep `budget` names with `/plans` paths internally (rejected by the user — they chose full plan terminology); keep `/budgets` (off-spec, rejected).

### Decision 2: `get_plan` returns a curated summary, not the full export
**Choice**: `get_plan(plan_id)` calls `GET /plans/{plan_id}` and maps `PlanDetail` to a `PlanDetailSummary`: plan metadata (`id`, `name`, `last_modified_on`, `first_month`, `last_month`), `currency_format`, `date_format`, and **counts** of the nested arrays (`accounts`, `category_groups`, `categories`, `payees`, `months`, `transactions`, `scheduled_transactions`).
**Why**: The full export can be enormous (every account/category/payee/month/transaction) and risks exceeding Claude's ~150k-char tool-result limit and flooding context. The summary gives an at-a-glance overview; the detailed records are already reachable via `list_accounts`/`list_categories`/`list_transactions`.
**Trade-off**: A caller wanting the raw export won't get it from this tool. Accepted; a dedicated/paginated export tool can be a later change if needed.
**Implementation note**: counts are computed from the parsed payload lengths (pure), so no extra requests.

### Decision 3: Default plan alias `"last-used"` (was `"default"`)
**Choice**: The `plan_id` default becomes `"last-used"`.
**Why**: Both aliases are valid, but `"default"` only resolves when the user has enabled "default plan selection" in YNAB; `"last-used"` always resolves to the most recently used plan. `"last-used"` is the more reliable zero-config default.
**Alternatives**: Keep `"default"` (can fail for users without the setting); require an explicit `plan_id` (more friction).

### Decision 4: Reuse the existing parser/client/tool pattern; add typed sub-models
**Choice**: Add frozen dataclasses `CurrencyFormat` and `DateFormat` (the fields YNAB returns: e.g. currency `iso_code`, `decimal_digits`, `symbol_first`, `currency_symbol`; date `format`), `PlanSettings` (currency + date format), and `PlanDetailSummary`. Pure `parse_plan_detail_summary` and `parse_plan_settings` map the envelopes; client methods do the I/O and delegate; tools wrap `client_from_env`.
**Why**: Consistency — same FP split, same `MockTransport` testing, same error/auth handling. New models stay typed and immutable.

## Risks / Trade-offs

- **Risk: the rename misses a call site**, leaving a stale `/budgets` path or `budget_id`. → Mitigation: the rename is mechanical and fully covered by updated tests that assert the new `/plans/...` paths via `MockTransport`; ruff/mypy catch dangling references; a repo-wide grep for `budget` in `src/` is part of the refactor step.
- **Risk: still can't prove correctness against the live API** (tests use mocks). → Mitigation: paths/aliases are now taken verbatim from the authoritative spec; an optional manual smoke test with a real token (never committed) is in the tasks.
- **Risk: `PlanDetail` field names differ from assumptions** (e.g. nested array keys). → Mitigation: keys are taken from the spec (`accounts`, `category_groups`, `categories`, `payees`, `months`, `transactions`, `scheduled_transactions`); parsers are defensive (missing array → count 0) and unit-tested with full and minimal payloads.
- **Trade-off: breaking tool rename.** → Accepted pre-1.0; called out in the proposal and README; warrants at least a minor version bump on the next release.

## Migration Plan

1. TDD the rename first (models/parsers/client/tools/tests + `/plans` paths + `last-used`), keeping the suite green at each step.
2. TDD the two new endpoints (summary + settings) bottom-up (parser → client → tool → register).
3. Update the README tool list and the `ynab-integration` living spec (MODIFY the tools requirement, ADD two).
- **Rollback**: revert the change; no persisted state. (Reverting restores the off-spec `/budgets` paths, so prefer fixing forward.)

## Open Questions

- None blocking. Whether to later add a full/paginated plan-export tool and delta sync remains an explicit non-goal here.
