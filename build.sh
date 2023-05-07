#!/usr/bin/env.sample bash
# exit on error
set -o errexit

python -m pip install --upgrade pip

pip install -r requirements.txt
