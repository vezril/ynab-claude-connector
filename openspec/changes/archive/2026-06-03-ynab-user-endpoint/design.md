## Context

The `ynab-integration` capability (Feature 3, shipped in v0.2.0) provides an async `YnabClient` over the YNAB API with bearer auth, a `data`-envelope unwrap, typed frozen-dataclass models + pure parsers, a typed error taxonomy, and four read-only MCP tools — all under a 90% coverage gate with ruff/mypy(strict) across Python 3.11–3.13. Feature 4 adds the YNAB **User** category, which is the single `GET /user` endpoint: `{"data": {"user": {"id": "<uuid>"}}}`. This is a small, additive extension that follows the exact pattern already established.

## Goals / Non-Goals

**Goals:**
- A `User` model + pure `parse_user`, a `YnabClient.get_user()` method, and a `get_user` MCP tool returning the authenticated user's id.
- Keep the established FP boundaries (pure parser; I/O confined to the client), full type hints, the 90% coverage floor, and ruff/mypy green.

**Non-Goals:**
- No new endpoints beyond `GET /user` (the User category has only one).
- No OAuth, write operations, delta sync, or new dependencies.

## Decisions

### Decision 1: Mirror the existing parser/model/client/tool pattern exactly
**Choice**: Add `User` as a `@dataclass(frozen=True, slots=True)` with a single `id: str` field; `parse_user(payload: Mapping) -> User` reads `payload["data"]["user"]["id"]` via the existing `_data` helper. `YnabClient.get_user()` does `parse_user(await self._get("user"))`. The `get_user` tool wraps `client_from_env` like the other tools.
**Why**: Consistency is the whole point — the same shapes, the same testing approach (`MockTransport`), the same error handling and auth come for free. No new concepts.
**Alternatives**: Returning a raw dict instead of a typed model — rejected; breaks the typed-model convention and the "no untyped surface" rule.

### Decision 2: `parse_user` returns a single `User`, not a tuple
**Choice**: Unlike the list endpoints, `GET /user` returns one object, so `parse_user` returns a single `User` (the tool returns `User`, not `tuple[User, ...]`).
**Why**: Matches the API's cardinality; a one-element tuple would be misleading.
**Edge case**: a malformed/empty body (missing `user`/`id`) should raise a clear error rather than silently returning an empty id — handled by treating the id as required (a `KeyError`-class failure surfaces as a tool error). This is consistent with required-field handling in the existing parsers.

## Risks / Trade-offs

- **Risk: unexpected/missing `user.id` in the payload.** → Mitigation: treat `id` as required and unit-test the malformed-payload case so the failure is explicit, not a silent empty value.
- **Trade-off: one more endpoint against the 200/hour limit.** → Negligible; the existing 429 → `YnabRateLimitError` mapping already covers it.
- **Risk: registering another tool could regress the server tool-count test.** → Mitigation: update `test_server.py` to expect the new tool name in the same change (TDD).

## Migration Plan

1. TDD bottom-up: `parse_user` (+ malformed edge case) → `YnabClient.get_user` (MockTransport, asserts `GET /user` + bearer) → `get_user` tool → register in `build_server`.
2. Update the README tool list and the `ynab-integration` living spec (via a delta with an added requirement).
- **Rollback**: additive; revert the change.

## Open Questions

- None. The User category is fully covered by `GET /user`.
