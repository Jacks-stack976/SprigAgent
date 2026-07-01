import { roundToCents } from "./currency";

/**
 * Apply a percentage discount (e.g. 0.1 for 10%) to an amount in cents.
 * Returns the discounted amount, in whole cents.
 */
export function applyPercentDiscount(cents: number, pct: number): number {
  if (pct < 0 || pct > 1) throw new Error("Discount pct must be between 0 and 1");
  return roundToCents(cents * (1 - pct));
}

/**
 * Allocate an integer-cent total across positive integer weights.
 * Stub — the coding agent implements this at eval time (task 002).
 */
export function allocateProportional(total: number, weights: number[]): number[] {
  throw new Error(`allocateProportional not implemented (total ${total}, ${weights.length} weights)`);
}
