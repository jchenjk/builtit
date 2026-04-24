#!/usr/bin/env bash
# Convenience script to run the backend in development.
set -e
cd "$(dirname "$0")"
uvicorn app.main:app --reload --port 8000
