def custom_hash(data, table_size=100, use_hex=False):
    hash_value = 0
    prime = 31

    for char in str(data):
        hash_value = (hash_value * prime + ord(char)) % table_size

    if use_hex:
        return format(hash_value, "04x")
    return hash_value
# Basic usage
print(custom_hash("apple"))              # e.g., 47
print(custom_hash("orange"))             # e.g., 12

# Change range to 1000
print(custom_hash("banana", table_size=1000))  # e.g., 841

# Get hex output
print(custom_hash("secret", use_hex=True))     # e.g., "005f"

# Hash numbers or mixed data
print(custom_hash(12345))                      # Works because of str()