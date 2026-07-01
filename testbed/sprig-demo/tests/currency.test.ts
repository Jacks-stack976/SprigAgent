import { describe, it, expect } from "vitest";
import { roundToCents, formatUSD } from "../src/currency";

describe("currency", () => {
  it("rounds fractional cents half-up", () => {
    expect(roundToCents(100.5)).toBe(101);
    expect(roundToCents(234.4)).toBe(234);
  });
  it("formats integer cents as USD", () => {
    expect(formatUSD(123450)).toBe("$1,234.50");
  });
});
