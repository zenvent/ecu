# Description: A long-running Python script to test abort functionality.
import time
import sys

print("Starting long running process...")
for i in range(100):
    print(f"Processing item {i+1}/100 - This is a lot of text to simulate a busy script outputting data.")
    sys.stdout.flush()
    time.sleep(0.5)

print("Finished.")
