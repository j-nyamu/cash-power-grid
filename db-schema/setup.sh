#!/usr/bin/env bash
# Usage: ./setup.sh <mysql_user>   (prompts for the password each time)
set -e
for f in 00_database.sql 01_auth.sql 02_meters.sql 03_usage.sql 04_activity.sql 05_changes.sql; do
  echo "Running $f"
  mysql -u "$1" -p < "$f"
done
echo "Done."