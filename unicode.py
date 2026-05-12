# 1. Simple Unicode string (no 'u' needed in Python 3)
text = "Café"
print(text)  # Output: Café

# 2. Using \u escape sequence
text = "Libert\u00e9"  # \u00e9 = é
print(text)  # Output: Liberté

# 3. Emoji (requires 8-digit \U)
emoji = "Party \U0001F389"
print(emoji)  # Output: Party 🎉

# 4. Multiple languages
multilang = "English: Hello, 中文: 你好, Español: Hola"
print(multilang)  # Works perfectly in Python 3

# 5. Checking your encoding
import sys
print(sys.stdout.encoding)  # Usually 'UTF-8' on modern systems