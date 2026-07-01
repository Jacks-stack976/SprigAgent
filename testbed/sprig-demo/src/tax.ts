import { roundToCents } from "./currency";

/**
 * Apply a tax rate (e.g. 0.08 for 8%) to a pre-tax amount in cents.
 * Returns the tax-inclusive total, in whole cents.
 */
export function applyTax(cents: number, rate: number): number {
  if (rate < 0) throw new Error("Tax rate cannot be negative");
  return roundToCents(cents * (1 + rate));
}
