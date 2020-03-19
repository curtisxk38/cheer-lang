#!/usr/bin/env bash

set -e

pytest --cov=cheer
mypy cheer
# flake8