# SprigAgent — credential-free replay demo.
# Prereqs: Python 3.10+ (ideally in an activated venv) and Node 18+.
#
#   make demo   -> one command: install + npm ci + serve the dashboard
#   make run    -> re-serve the dashboard without reinstalling
#   make test   -> full pytest, incl. the vitest success-rate half over the bundled testbed

.PHONY: demo setup run test

# The single judge entry point: one setup step, then one run step.
demo: setup run

# One setup step: editable install + the bundled testbed's Node deps (one-time).
setup:
	python -m pip install -e .
	cd testbed/sprig-demo && npm ci

# One run step: replay defaults the model from the committed cache, so NO env vars / creds.
run:
	SPRIG_DRIVER=replay python -m sprigagent.ui ./testbed/sprig-demo

# The success-rate half (4/4, 3/4) needs vitest; point the harness at the bundled testbed.
test:
	SPRIG_DEMO_REPO=./testbed/sprig-demo python -m pytest
