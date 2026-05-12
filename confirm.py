import os

filename = 'output.txt'

# Check if file exists
if os.path.exists(filename):
    print(f"✅ File exists: {os.path.abspath(filename)}")
    print(f"📏 Size: {os.path.getsize(filename)} bytes")

    # Preview first 3 lines
    with open(filename, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:
                break
            print(f"Line {i + 1}: {repr(line)}")
else:
    print(f"❌ File not found: {filename}")