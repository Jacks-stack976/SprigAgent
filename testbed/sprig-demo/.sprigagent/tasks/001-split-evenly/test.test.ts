import { describe, it, expect } from "vitest";
import { splitEvenly } from "../../../src/invoice";

describe("task-001 splitEvenly", () => {
  it("puts the leftover on the earliest shares", () => {
    expect(splitEvenly(1000, 3)).toEqual([334, 333, 333]);
    expect(splitEvenly(100, 3)).toEqual([34, 33, 33]);
  });
  it("splits cleanly when divisible", () => {
    expect(splitEvenly(1000, 4)).toEqual([250, 250, 250, 250]);
  });
  it("the shares always sum back to the total", () => {
    const parts = splitEvenly(1000, 3);
    expect(parts.reduce((a, b) => a + b, 0)).toBe(1000);
  });
  it("throws when parts is less than 1", () => {
    expect(() => splitEvenly(100, 0)).toThrow();
  });
});
