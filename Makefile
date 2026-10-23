# Local quality gate. CI replays the same checks; this is the first line.
VENV := .venv
PY := $(VENV)/bin/python

# Pinned by version AND digest; refresh with:
#   docker pull semgrep/semgrep:<x.y.z> && docker inspect --format '{{index .RepoDigests 0}}' semgrep/semgrep:<x.y.z>
SEMGREP_IMAGE := semgrep/semgrep:1.181.1@sha256:3db5c7af55eb1f512eac0abf0ab69a97b52c74b5e9a27314c221aee1a78d7ab2
SEMGREP_RULES := --config p/python --config p/flask
# In a git worktree .git points outside the mount; Semgrep needs it to scan tracked files only.
GIT_COMMON_DIR := $(abspath $(shell git rev-parse --git-common-dir))

.PHONY: venv lint typecheck test sast scan-secrets sonar-scan check-local

venv:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install "setuptools<81" -e . -r requirements-dev.txt

lint:
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .

typecheck:
	$(VENV)/bin/mypy trading_bot tests

test:
	$(VENV)/bin/pytest tests/ --cov=trading_bot --cov=scripts --cov-report=term-missing --cov-report=xml

sast:
	docker run --rm -u "$$(id -u):$$(id -g)" -e HOME=/tmp \
		-v "$(CURDIR)":/src:ro -w /src -v "$(GIT_COMMON_DIR)":"$(GIT_COMMON_DIR)":ro $(SEMGREP_IMAGE) \
		semgrep scan $(SEMGREP_RULES) --metrics=off --disable-version-check --error

scan-secrets:
	gitleaks git --redact --no-banner .

# Uses the global analysis token from the environment (SONAR_TOKEN); never commit it.
sonar-scan: test
	sonar-scanner

check-local: lint typecheck test sast scan-secrets
