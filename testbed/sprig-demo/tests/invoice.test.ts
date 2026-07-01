import { describe, it, expect } from "vitest";
import { subtotal, invoiceTotal } from "../src/invoice";

describe("invoice", () => {
  it("sums line items (in cents)", () => {
    expect(
      subtotal([
        { description: "a", quantity: 2, unitPriceCents: 1000 },
        { description: "b", quantity: 1, unitPriceCents: 500 },
      ]),
    ).toBe(2500);
  });
  it("applies discount then tax", () => {
    // 2500c -> -10% = 2250c -> +8% = 2430c
    expect(
      invoiceTotal({
        items: [{ description: "a", quantity: 5, unitPriceCents: 500 }],
        taxRate: 0.08,
        discountPct: 0.1,
      }),
    ).toBe(2430);
  });
});
