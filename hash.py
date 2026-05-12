import hashlib

def verify_hash(target_hash, wordlist_path, algorithm="sha256"):
    with open(wordlist_path, "r", encoding="utf-8", errors="ignore") as wordlist:
        for line in wordlist:
            candidate = line.strip()
            computed_hash = hashlib.new(algorithm, candidate.encode()).hexdigest()
            if computed_hash == target_hash.lower():
                return candidate
    return None