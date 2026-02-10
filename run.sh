#!/bin/bash
set -e

uv python install 3.14

uv venv --python 3.14
uv sync

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
