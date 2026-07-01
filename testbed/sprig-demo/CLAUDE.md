# CLAUDE.md

Context for coding agents working in this repo.

## Project
`sprig-demo` is a small TypeScript invoicing toolkit (subtotal -> discount -> tax).
Pure functions in `src/`, tests in `tests/`. No framework, no network calls.

## Money convention (load-bearing)
- **All monetary amounts are integer cents.** `1000` means $10.00. Prices, subtotals,
  tax, discounts, and totals are whole numbers of cents — never floating-point dollars.
- **Never do money math in floating-point dollars.** Float arithmetic drifts and loses
  pennies (`0.1 + 0.2 !== 0.3`). Keep every intermediate value in integer cents.
- **Convert to dollars only at the display edge**, via `formatUSD` in `currency.ts`.
- **When dividing money that does not split evenly, give the leftover cents to the
  earliest shares**, so the parts always sum back to the exact whole.

## Commands
- Install: `npm install`
- Run: `npm start`
- Test: `npm test`
- Typecheck: `npm run typecheck`
- Lint: `npm run lint`

## Working agreements
- **Always run `npm run typecheck` after editing and fix every error before you finish.**
  This codebase is in strict mode; a single loose type silently breaks downstream callers.
- Run `npm test` before declaring a task done. A task is not complete until its test passes.
- Keep money math in `currency.ts`; never hand-roll rounding elsewhere.
- New helpers go in the matching module (`tax.ts`, `discount.ts`, etc.), not in `index.ts`.

## Canonical references
- The canonical tax logic lives in `src/legacy/payments.ts` — read it before touching tax.

## Code style
- Use 2-space indentation everywhere.
- Use double quotes for all strings.
- Always end statements with a semicolon.
- Add trailing commas on all multi-line literals and parameter lists.
- Keep lines under 80 characters.
- Always put one space inside curly braces: `{ foo }` not `{foo}`.
- Never leave trailing whitespace at the end of a line.
- Always end every file with a single newline.
- Order imports: node built-ins first, then third-party, then local.
- Use `const` by default; only use `let` when reassignment is required.
- Prefer arrow functions for callbacks passed to array methods.
- Name booleans with an `is`/`has`/`should` prefix.
- Use `camelCase` for variables and functions, `PascalCase` for types.
- Do not use `var` anywhere in the codebase.
- Avoid abbreviations in identifiers except well-known ones like `id` and `url`.
