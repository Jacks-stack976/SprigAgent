# GEMINI.md

Notes for Gemini-based coding sessions in `sprig-demo`.

## Overview
A tiny TypeScript invoicing library. Deterministic, no I/O. See `src/` for modules.

## How to verify your work
- `npm run typecheck` must pass.
- `npm test` must pass.

## Formatting
- Indent with 4 spaces.
- Strings should use double quotes.
- End every statement with a semicolon.

## Notes
- Tax and discount are applied in that order: discount first, then tax.
