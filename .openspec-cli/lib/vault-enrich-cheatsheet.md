# Vault enrichment cheatsheet (clipboard agents)

Keep enrichment concise. Only include what a developer needs for this ticket.

## Hard rules
- Money: always `Decimal`, never `float`
- Datetime: use `hook_arguments.effective_datetime` (`ZoneInfo`); never `import datetime`
- Sandbox: no `os/sys/json/re/requests/open/print/eval`
- API 4.0: `Rejection` (return, don't raise); no `client_transaction_id` on `CustomInstruction`
- Phase lives on `BalanceCoordinate`, not on `Balance`
- Tests: `os-vault-test` and `os-vault-test --coverage` (>= 90%)

## Typical hooks to consider
`activation_hook`, `pre_posting_code`, `post_posting_code`, `scheduled_event_hook`, derived parameters when needed

## Typical files
`contracts/<name>.py`, `tests/test_<name>.py`
