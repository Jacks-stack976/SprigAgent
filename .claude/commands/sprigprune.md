---
description: Find this repo's instruction files and prune them with SprigAgent (proven cuts, human-approved).
---

You are helping prune the instruction files in this repository using SprigAgent. SprigAgent proves each cut is safe against the repo's own tests before surfacing it, and a human approves every change. Do not edit any instruction file yourself. Run SprigAgent and let its proven, human-approved flow do the pruning.

Follow these steps:

1. Check that SprigAgent is installed by running `python -m sprigagent --help`. If it is not installed and this is the SprigAgent repository, run `pip install -e .` first.

2. Check that this repo has something for SprigAgent to prove against: either a `.sprigagent/` eval setup or a normal test suite. If it has neither, stop and tell me plainly that SprigAgent needs an independent test suite to prove cuts are safe and will not invent one. Point me to the "Run it on your own repo" section of the SprigAgent README.

3. List the instruction files present in the repo, for example CLAUDE.md, GEMINI.md, AGENTS.md, or .cursorrules.

4. Start the approval dashboard for the main instruction file:
   `python -m sprigagent.ui . --file CLAUDE.md`
   Use the real file name. For the bundled sample project, prefix the command with `SPRIG_DRIVER=replay` to run credential-free. For live proving on my own code, make sure the Vertex variables from `.env.example` are set.

5. Tell me to open http://127.0.0.1:8765 and approve or decline each proven cut.

6. If there are several instruction files, repeat step 4 for each one.

Report which files you ran, and remind me that nothing changes until I approve it in the dashboard.
