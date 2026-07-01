import { describe, it, expect } from "vitest";
import { isValidQuantity } from "../../../src/validate";

describe("task-004 isValidQuantity", () => {
  it("accepts positive integers", () => {
    expect(isValidQuantity(3)).toBe(true);
  });
  it("rejects zero, negatives, and decimals", () => {
    expect(isValidQuantity(0)).toBe(false);
    expect(isValidQuantity(-2)).toBe(false);
    expect(isValidQuantity(2.5)).toBe(false);
  });
});
