import hashlib
import sys

def generate_hash(text: str, algorithm: str = "sha256") -> str:
    """Return a hexadecimal hash of the input text using the specified algorithm."""
    # Hash functions require bytes, not strings
    data = text.encode("utf-8")
    # Create a hash object for the chosen algorithm and compute the digest
    return hashlib.new(algorithm, data).hexdigest()

if __name__ == "__main__":
    # Default algorithm
    algorithm = "sha256"

    # Allow optional command-line argument to override algorithm
    if len(sys.argv) > 1:
        algorithm = sys.argv[1]

    # Get input from user
    plaintext = input("Enter text to hash:mySecretPass123 ")

    try:
        result = generate_hash(plaintext, algorithm)
        print(f"\nAlgorithm : {algorithm.upper()}")
        print(f"Input     : {plaintext}")
        print(f"Hash      : {result}")
    except ValueError as e:
        print(f"\n❌ Unsupported algorithm: {algorithm}")
        print(f"Valid options: {', '.join(hashlib.algorithms_available)}")