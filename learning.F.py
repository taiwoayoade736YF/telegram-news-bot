# basic struture of core function syntax
def function_name(parameter1, parameter2, ):
    """Docstring describing what the function does"""
    # Function body (indented)
    result = parameter1 + parameter2
    return result  # ← Returns an object to the caller

# more examples
def with_print(x):
    print(x * 2)  # ← Only displays output

def with_return(x):
    return x * 2  # ← Sends value back for reuse

# Usage:
with_print(5)     # Output: 10 (but returns None!)
result = with_print(5)  # result = None ❌

with_return(5)    # No output (but returns 10)
result = with_return(5)  # result = 10 ✅
print(result)     # Output: 10

# RETURN A SINGLE VALUE

def square(x):
    """Return the square of x"""
    return x * x
result = square(2)

#  Return Multiple Values (Actually Returns a Tuple)
def get_user():
    name = "Alice"
    age = 30
    city = "Paris"
    return name, age, city  # ← Returns tuple: ("Alice", 30, "Paris")

# Unpack the tuple:
user_name, user_age, user_city = get_user()
print(user_name)  # "Alice"

# Return a Dictionary (Best for Named Multiple Values)

def get_user_dict():
    return {
        "name": "Alice",
        "age": 30,
        "city": "Paris"
    }

user = get_user_dict()
print(user["name"])  # "Alice"

# 🧠 Mental Model: A Function is a Reusable Recipe

def double(x):
    result = x * 2
    return result
    meal = double(5)
    print(meal)
