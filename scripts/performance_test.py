# Description: Generates complex output with mixed log levels and line lengths to stress test the UI.
import time
import random
import string
import sys

print("Starting complex performance test...")
start_time = time.time()

# Log levels and their probabilities
# mostly normal logs (INFO)
log_levels = ["INFO", "WARNING", "ERROR", "CRITICAL", "DEBUG"]
weights = [0.7, 0.15, 0.1, 0.02, 0.03]

def generate_random_string(length):
    return ''.join(random.choices(string.ascii_letters + string.digits + " ", k=length))

for i in range(1, 100001):
    level = random.choices(log_levels, weights=weights)[0]
    
    # Determine line length
    # mostly normal length (20-100 chars), some long (1000+ chars)
    if random.random() < 0.05: # 5% chance of very long line
        length = random.randint(1000, 5000)
        msg_type = "LONG_MSG"
    else:
        length = random.randint(20, 100)
        msg_type = "MSG"

    message = generate_random_string(length)
    
    # Construct log line
    # Format: [LEVEL] Line N: Message...
    log_line = f"[{level}] Line {i} ({msg_type}): {message}"
    
    # Print to stdout (or stderr for errors sometimes)
    if level in ["ERROR", "CRITICAL"] and random.random() < 0.5:
        print(log_line, file=sys.stderr)
    else:
        print(log_line)
        
    # Occasionally sleep slightly to simulate real work (very minimal)
    if i % 1000 == 0:
        # print(f"--- {i} lines processed ---", file=sys.stderr)
        pass

end_time = time.time()
duration = end_time - start_time
print(f"Performance test completed in {duration:.4f} seconds.")
