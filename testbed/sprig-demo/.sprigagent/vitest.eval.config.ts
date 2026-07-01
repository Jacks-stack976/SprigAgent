import { defineConfig } from "vitest/config";

// Used by SprigAgent's Eval-Runner to execute the frozen task tests after the
// coding agent has implemented each task. These hidden tests are NOT part of the
// baseline suite (see ../vitest.config.ts). Run from the repo root, e.g.:
//   npx vitest run --config .sprigagent/vitest.eval.config.ts \
//     .sprigagent/tasks/001-split-evenly/test.test.ts
export default defineConfig({
  test: {
    include: [".sprigagent/tasks/**/*.test.ts"],
  },
});
