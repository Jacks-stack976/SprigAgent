import { describe, it, expect } from "vitest";
import { applyPercentDiscount } from "../src/discount";

describe("applyPercentDiscount", () => {
  it("applies a percentage off (cents in, cents out)", () => {
    expect(applyPercentDiscount(10000, 0.1)).toBe(9000);
  });
  it("rejects out-of-range pct", () => {
    expect(() => applyPercentDiscount(10000, 1.5)).toThrow();
  });
});
