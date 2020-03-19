#!/usr/bin/env bash

set -e

pytest
mypy cheer
flake8