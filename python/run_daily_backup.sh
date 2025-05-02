#!/bin/bash

echo "=== Running AWS Backup at $(date) ==="

cd /path/to/aws-infra-lab/python || exit 1

# Use the correct Python path
/Library/Frameworks/Python.framework/Versions/3.12/bin/python3 ec2_snapshot_backup.py --prune

echo "=== Finished ==="
