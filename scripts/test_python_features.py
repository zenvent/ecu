import sys
import time

# Description: Comprehensive test for Python script features: Flags, Colors, Stderr, Input.
# Flags: dev, test, prod, input, error

def print_log(message, type="INFO"):
    print(f"[{type}] {message}")
    sys.stdout.flush()

print("Starting Python Features Test...")
print(f"Arguments received: {sys.argv[1:]}")

# --- Flags Test ---
if 'dev' in sys.argv:
    print_log("Running in DEV mode", "INFO")
if 'test' in sys.argv:
    print_log("Running in TEST mode", "INFO")
if 'prod' in sys.argv:
    print_log("Running in PROD mode", "INFO")

# --- Colors Test ---
print_log("This is a standard informational message.", "INFO")
print_log("This is a warning message that should be yellow/orange.", "WARNING")
print_log("This is an error message that should be red.", "ERROR")
print("This is a normal text line without any specific tag.")

# --- Stderr Test ---
if 'error' in sys.argv:
    print("Testing stderr output...", file=sys.stderr)
    sys.stderr.write("This is written directly to stderr.\n")
    sys.stderr.flush()

# --- Input Test ---
if 'input' in sys.argv:
    print("Input requested. Please enter something:")
    sys.stdout.flush()
    try:
        user_input = sys.stdin.readline().strip()
        print(f"You entered: {user_input}")
    except Exception as e:
        print(f"Error reading input: {e}")

print("Python Features Test Complete.")
