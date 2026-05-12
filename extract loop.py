import time
from datetime import datetime


def extract_and_save(param, param1):
    pass


try:
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        print(f"[{timestamp}] 🔄 Starting scrape...")

        try:
            extract_and_save('https://fqluxury.org', f'output_{timestamp}.txt')
            print(f"[{timestamp}] ✅ Success!")
        except Exception as e:
            print(f"[{timestamp}] ❌ Failed: {e}")

        print(f"[{timestamp}] 😴 Waiting 30 minutes...\n")
        time.sleep(1800)

except KeyboardInterrupt:
    print("\n🛑 Ctrl+C detected. Stopping gracefully...")
    # Optional: cleanup code here
    print("✅ Exit complete.")