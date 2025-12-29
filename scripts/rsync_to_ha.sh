#!/bin/bash
# Helper script to rsync code to Home Assistant, excluding venv and other unnecessary files

rsync -avz -e ssh --rsync-path="sudo rsync" \
  --exclude='venv' \
  --exclude='.venv' \
  --exclude='env' \
  --exclude='.env' \
  --exclude='ENV' \
  --exclude='.ENV' \
  --exclude='scripts/venv' \
  --exclude='scripts/venv/' \
  --exclude='**/venv' \
  --exclude='**/venv/' \
  --exclude='__pycache__' \
  --exclude='**/__pycache__' \
  --exclude='*.pyc' \
  --exclude='*.pyo' \
  --exclude='*.pyd' \
  --exclude='.git' \
  --exclude='.gitignore' \
  --exclude='.pytest_cache' \
  --exclude='.coverage' \
  --exclude='htmlcov' \
  --exclude='.tox' \
  --exclude='.hypothesis' \
  --exclude='.vscode' \
  --exclude='.idea' \
  --exclude='*.swp' \
  --exclude='*.swo' \
  --exclude='*~' \
  --exclude='.DS_Store' \
  --exclude='Thumbs.db' \
  --exclude='*.log' \
  --exclude='logs' \
  --exclude='dist' \
  --exclude='build' \
  --exclude='*.egg-info' \
  --exclude='.history' \
  . 11warenda@homeassistant:/config/custom_components/versatile_thermostat-dev/
