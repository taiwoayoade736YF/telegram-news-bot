import hashlib

def verify_hash(target_hash, wordlist_path, algorithm="sha256"):
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as wordlist:
        for line in wordlist:
            candidate = line.strip()
            computed_hash = hashlib.new(algorithm, candidate.encode()).hexdigest()
            if computed_hash == target_hash.lower():
                return candidate
    return None

# --- How to call and use the function ---
if __name__ == "__main__":
    # 1. The hash you want to test (must be a valid hex string)
    target = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"

    # 2. Path to your wordlist file (one candidate per line)
    wordlist_file = "wordlist.txt"  # Replace with your authorized file path

    # 3. Call the function
    recovered = verify_hash(target, wordlist_file, algorithm="sha256")

    # 4. Handle the output
    if recovered:
        print(f"[+] Match found: {recovered}")
    else:
        print("[-] No match found in the provided wordlist.")

