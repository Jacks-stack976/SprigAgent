export interface LineItem {
  description: string;
  quantity: number;
  unitPriceCents: number;
}

/** Throw if a line item is structurally invalid. */
export function validateLineItem(item: LineItem): void {
  if (!item.description.trim()) throw new Error("Line item needs a description");
  if (item.quantity <= 0) throw new Error("Quantity must be positive");
  if (item.unitPriceCents < 0) throw new Error("Unit price cannot be negative");
}

/**
 * Return true only for positive integers (no zero, negatives, or decimals).
 * Stub — the coding agent implements this at eval time (task 004).
 */
export function isValidQuantity(n: number): boolean {
  throw new Error(`isValidQuantity(${n}) not implemented`);
}
