---
name: playwright-ui-self-check
description: Execute Playwright MCP smoke checks for uni-app + Vue frontend pages after UI/layout/style/text changes, verify page load and console errors, and iterate until frontend syntax/template/compiler errors are cleared.
---

# Playwright UI Self Check

## Scope
- Use this skill after any changes to:
- `pages/**/*.vue`
- `App.vue`
- `uni.scss`
- `pages.json`
- Any UI text, layout, style, or component structure.

## Execution Steps
1. Build target page list.
- Always include:
- `/pages/agent/chat`
- `/pages/agent/conversation`
- `/pages/patient/list`
- `/pages/patient/detail`
- Add all pages touched in this change set.

2. Navigate and inspect.
- For each page:
- Run `browser_navigate` to page URL.
- Run `browser_console_messages` with `level: "error"`.
- If dynamic import or compile error appears, run `browser_snapshot` to capture exact file/line.

3. Fix and loop.
- If error is frontend syntax/template/compiler/runtime issue (e.g. `Element is missing end tag`, `Unexpected token`, `Unterminated string`), fix code immediately and re-run checks.
- Repeat until frontend errors are zero on checked pages.

4. Classify non-frontend errors.
- If errors are backend/environment issues (CORS, network timeout, 5xx, backend unavailable), mark as environment issue.
- Do not treat backend connectivity errors as UI self-check failure.

## Pass Criteria
- All checked pages can be opened.
- Console has no frontend compile/runtime syntax errors.
- Remaining errors (if any) are explicitly labeled backend/environment.

## Report Template
- Checked pages:
- Frontend errors fixed:
- Remaining environment issues:
- Final status: pass / blocked-by-environment
