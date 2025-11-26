#!/bin/bash
# Description: A test shell script.
# Flags: all, quiet, dry-run

echo "Starting Shell Script..."
echo "Arguments: $@"

for arg in "$@"
do
    if [ "$arg" == "all" ]; then
        echo "Processing ALL items"
    elif [ "$arg" == "quiet" ]; then
        echo "Quiet mode enabled"
    elif [ "$arg" == "dry-run" ]; then
        echo "Dry run - no changes will be made"
    fi
done

echo "Working..."
sleep 2
echo "Done."
