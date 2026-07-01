import { applyTax } from "./tax";
import { applyPercentDiscount } from "./discount";
import { validateLineItem, type LineItem } from "./validate";

export interface InvoiceInput {
  items: LineItem[];
  taxRate: number;
  discountPct: number;
}

/** Compute the subtotal of all line items (qty * unitPriceCents), in whole cents. */
export function subtotal(items: LineItem[]): number {
  return items.reduce((sum, it) => {
    validateLineItem(it);
    return sum + it.quantity * it.unitPriceCents;
  }, 0);
}

/** Build a final invoice total in cents: subtotal -> discount -> tax. */
export function invoiceTotal(input: InvoiceInput): number {
  const base = subtotal(input.items);
  const discounted = applyPercentDiscount(base, input.discountPct);
  return applyTax(discounted, input.taxRate);
}

/**
 * Split an integer-cent total into `parts` as-equal-as-possible shares.
 * Stub — the coding agent implements this at eval time (task 001).
 */
export function splitEvenly(total: number, parts: number): number[] {
  throw new Error(`splitEvenly(${total}, ${parts}) not implemented`);
}
