import sys
import time

# Description: A test script to verify flag passing.
# Flags: dev, test, prod

print("Starting Flag Test Script...")
print(f"Arguments received: {sys.argv[1:]}")

if 'dev' in sys.argv:
    print("Running in DEV mode")
if 'test' in sys.argv:
    print("Running in TEST mode")
if 'prod' in sys.argv:
    print("Running in PROD mode")

for i in range(3):
    print(f"Working... {i+1}")
    time.sleep(0.5)

print("Done.")
