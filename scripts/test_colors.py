import sys
import time

def print_log(message, type="INFO"):
    print(f"{type}: {message}")
    sys.stdout.flush()
    time.sleep(0.5)

print("Starting Color Test...")
print_log("This is a standard informational message.", "INFO")
print_log("This is a warning message that should be yellow/orange.", "WARNING")
print_log("This is an error message that should be red.", "ERROR")
print("This is a normal text line without any specific tag.")
print("CRITICAL: This is a critical error!", end="\n")
sys.stderr.write("This is written to stderr, which should also be red.\n")
print("Test Complete.")
