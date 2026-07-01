# Task 003 — euro formatting

Add an exported function `formatEUR(cents: number): string` to
`src/currency.ts`.

Given an integer-cent amount, format it as euros using `Intl.NumberFormat` with
locale `"de-DE"` and currency `"EUR"` (e.g. `123450` renders as `"1.234,50 €"`).
