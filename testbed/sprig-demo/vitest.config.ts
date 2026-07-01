import { defineConfig } from "vitest/config";

// Baseline suite only. The .sprig/tasks/*.test.ts files are NOT run here —
// they are run on demand by SprigAgent's Eval-Runner after the coding agent
// has implemented each task, e.g. `vitest run .sprig/tasks/task-01.test.ts`.
export default defineConfig({
  test: {
    include: ["tests/**/*.test.ts"],
  },
});
