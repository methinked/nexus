
import time
import psutil

def test_blocking():
    print("Testing blocking call (interval=1.0)...")
    start = time.time()
    cpu = psutil.cpu_percent(interval=1.0)
    end = time.time()
    duration = end - start
    print(f"Duration: {duration:.4f}s (Should be >= 1.0s)")
    print(f"CPU: {cpu}%")
    return duration

def test_non_blocking():
    print("\nTesting non-blocking call (interval=0)...")
    # First call - initializes
    psutil.cpu_percent(interval=None)
    
    start = time.time()
    # Simulate some work or sleep
    time.sleep(0.1)
    cpu = psutil.cpu_percent(interval=0)
    end = time.time()
    duration = end - start
    print(f"Duration: {duration:.4f}s (Should be << 1.0s, close to 0.1s)")
    print(f"CPU: {cpu}%")
    return duration

if __name__ == "__main__":
    blocking_time = test_blocking()
    non_blocking_time = test_non_blocking()
    
    if non_blocking_time < 0.2 and blocking_time >= 1.0:
        print("\n✅ Verification SUCCESS: Logic switched to non-blocking.")
    else:
        print("\n❌ Verification FAILED: Timing unexpectedly similar.")
