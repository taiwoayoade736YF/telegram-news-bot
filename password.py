import hashlib
import re
import time
import secrets


def check_password_strength(password: str) -> dict:
    """Evaluate password strength and return feedback."""
    feedback = []
    score = 0
    if len(password) >= 12:
        score += 1
    else:
        feedback.append("Should be at least 12 characters long")
    if re.search(r"[A-Z]", password):
        score += 1
    else:
        feedback.append("Add at least one uppercase letter")
    if re.search(r"[a-z]", password):
        score += 1
    else:
        feedback.append("Add at least one lowercase letter")
    if re.search(r"\d", password):
        score += 1
    else:
        feedback.append("Add at least one digit")
    if re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        score += 1
    else:
        feedback.append("Add at least one special character")

    strength = "Weak" if score <= 2 else "Medium" if score <= 4 else "Strong"
    return {"strength": strength, "score": score, "feedback": feedback}


def simulate_secure_check(attempt: str, stored_hash: str, salt: str, algorithm: str = "sha256") -> bool:
    """
    Simulates secure password verification.
    In production, use bcrypt/Argon2 via dedicated libraries.
    Includes a deliberate delay to simulate server-side rate limiting.
    """
    time.sleep(0.5)  # Simulate rate limiting / anti-automation defense

    h = hashlib.new(algorithm)
    h.update((salt + attempt).encode())
    return h.hexdigest() == stored_hash


# 🔐 Example Usage (Educational Only)
if __name__ == "__main__":
    print("⚠️  This script is for educational and authorized testing purposes only.")
    print("Never attempt to access systems without explicit, written permission.\n")

    # Simulate a stored credential (in reality, this comes from a secure database)
    PASSWORD = "MyS3cureP@ss!"
    SALT = secrets.token_hex(16)

    h = hashlib.sha256()
    h.update((SALT + PASSWORD).encode())
    STORED_HASH = h.hexdigest()

    # Check strength
    result = check_password_strength(PASSWORD)
    print(f"🔍 Password Strength: {result['strength']} ({result['score']}/5)")
    for msg in result['feedback']:
        print(f"   • {msg}")
    print()

    # Simulate verification
    attempts = ["password123", "MyS3cureP@ss!", "admin"]
    for attempt in attempts:
        print(f"🔑 Trying: {attempt}")
        if simulate_secure_check(attempt, STORED_HASH, SALT):
            print("   ✅ Match found")
        else:
            print("   ❌ Incorrect")
        print()