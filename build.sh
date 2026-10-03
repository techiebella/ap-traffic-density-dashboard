#!/usr/bin/env bash

set -o errexit

pip install -r requirements.txt

python traffic_dashboard/manage.py collectstatic --noinput

python traffic_dashboard/manage.py migrate