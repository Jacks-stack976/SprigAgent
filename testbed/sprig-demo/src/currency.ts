// Money helpers for the invoicing toolkit.
// All monetary amounts are integer cents (1000 = $10.00). Floating-point dollars
// are only used at the display edge, in formatUSD below.

/**
 * Round a fractional-cent amount (e.g. the result of a tax or discount calc) to a
 * whole cent, half-up. Inputs and outputs are in cents.
 */
export function roundToCents(amount: number): number {
  return Math.round(amount + Number.EPSILON);
}

/** Format an integer-cent amount as a USD string, e.g. 123450 -> "$1,234.50". */
export function formatUSD(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

/**
 * Format an integer-cent amount as euros (de-DE locale).
 * Stub — the coding agent implements this at eval time (task 003).
 */
export function formatEUR(cents: number): string {
  throw new Error(`formatEUR(${cents}) not implemented`);
}
