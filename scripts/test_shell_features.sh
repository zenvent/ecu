#!/bin/bash
# Description: Comprehensive test for Shell script features: Flags, Colors, Input.
# Flags: dev, test, prod, input, error

echo "Starting Shell Features Test..."
echo "Arguments: $@"

# --- Flags Test ---
for arg in "$@"
do
    if [ "$arg" == "dev" ]; then
        echo "[INFO] Running in DEV mode"
    elif [ "$arg" == "test" ]; then
        echo "[INFO] Running in TEST mode"
    elif [ "$arg" == "prod" ]; then
        echo "[INFO] Running in PROD mode"
    fi
done

# --- Colors Test ---
echo "[INFO] This is an info message (should be blueish)"
echo "[WARNING] This is a warning message (should be yellowish)"
echo "[ERROR] This is an error message (should be reddish)"
echo "This is a normal message."

# --- Stderr Test ---
if [[ " $@ " =~ " error " ]]; then
    echo "Testing stderr output..." >&2
    echo "This is written to stderr." >&2
fi

# --- Input Test ---
if [[ " $@ " =~ " input " ]]; then
    echo "Input requested. Please enter something:"
    read user_input
    echo "You entered: $user_input"
else
    echo "No input flag detected, skipping input test."
fi

echo "Shell Features Test Complete."
