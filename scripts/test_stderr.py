import sys
import time

print("This is normal stdout output.")
sys.stdout.flush()
time.sleep(0.5)
print("This is stderr output which should be red.", file=sys.stderr)
sys.stderr.flush()
time.sleep(0.5)
print("Back to normal stdout.")
