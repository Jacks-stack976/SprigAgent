import { describe, it, expect } from "vitest";
import { formatEUR } from "../../../src/currency";

describe("task-003 formatEUR", () => {
  it("formats integer cents as euros (de-DE)", () => {
    // de-DE renders 123450 cents as "1.234,50 €"
    expect(formatEUR(123450)).toContain("1.234,50");
    expect(formatEUR(123450)).toContain("€");
  });
});
