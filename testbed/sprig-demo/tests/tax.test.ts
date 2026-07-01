import { describe, it, expect } from "vitest";
import { applyTax } from "../src/tax";

describe("applyTax", () => {
  it("adds the tax rate (cents in, cents out)", () => {
    expect(applyTax(10000, 0.08)).toBe(10800);
  });
  it("rejects negative rates", () => {
    expect(() => applyTax(10000, -0.1)).toThrow();
  });
});
