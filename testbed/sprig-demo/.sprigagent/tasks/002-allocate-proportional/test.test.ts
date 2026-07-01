import { describe, it, expect } from "vitest";
import { allocateProportional } from "../../../src/discount";

describe("task-002 allocateProportional", () => {
  it("allocates in proportion to the weights", () => {
    expect(allocateProportional(1000, [2, 1, 1])).toEqual([500, 250, 250]);
    expect(allocateProportional(1000, [3, 1])).toEqual([750, 250]);
  });
  it("distributes leftover cents so the parts sum to the total", () => {
    expect(allocateProportional(1000, [1, 1, 1])).toEqual([334, 333, 333]);
    expect(allocateProportional(100, [1, 1, 1])).toEqual([34, 33, 33]);
    const parts = allocateProportional(1000, [1, 1, 1]);
    expect(parts.reduce((a, b) => a + b, 0)).toBe(1000);
  });
  it("rejects empty or non-positive weights", () => {
    expect(() => allocateProportional(1000, [])).toThrow();
    expect(() => allocateProportional(1000, [1, 0, 2])).toThrow();
  });
});
