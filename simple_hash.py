def simple_hash(key, table_size):
    hash_value = 0
    for char in key:
        hash_value = (hash_value * 31 + ord(char)) % table_size
    return hash_value
print(simple_hash("cat", 10))  # Might output: 4
print(simple_hash("dog", 10))  # Might output: 7