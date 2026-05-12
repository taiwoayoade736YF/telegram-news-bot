# test_token.py
TOKEN = "8641134115:AAF09GeiU0xzIFjhDlMHYWzLhUEGZK1VyzU"
print(f"Token: '{TOKEN}'")
print(f"Length: {len(TOKEN)}")
print(f"Has colon: {':' in TOKEN}")
print(f"Valid: {bool(TOKEN and len(TOKEN) >= 40 and ':' in TOKEN)}")