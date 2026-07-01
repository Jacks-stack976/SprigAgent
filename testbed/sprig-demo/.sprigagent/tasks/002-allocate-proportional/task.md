# Task 002 — allocate a total across weights

Add an exported function
`allocateProportional(total: number, weights: number[]): number[]` to
`src/discount.ts`.

It splits `total` across the given positive integer `weights` in proportion to
each weight, returning one share per weight. Throw if `weights` is empty or
contains a value that is not a positive number.
