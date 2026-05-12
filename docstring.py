from http.client import responses


def printme(me):
    """
print (its argument.)
"""
    print(me)

help(printme)

# ✅ Define the variable first
statement = "We no guide frequently"  # Or get input from user/API/etc.

# Now the comparison works
if statement == "We no guide frequently":
    response = "Oh we guide sha"
elif statement == "We have rice here sir":
    response = "Oh we have rice here sir"
else:
    response = "Oh we have rice here sir eje"

print(response)


weather = "sunny"

if weather == "rainy":
    print("Take an umbrella")
elif weather == "sunny":          # ← Checked because first condition was False
    print("Wear sunglasses")      # ✅ This runs
elif weather == "snowy":
    print("Wear a coat")

#another example
    weather = "cloudy"

    if weather == "rainy":
        print("Take an umbrella")
    elif weather == "sunny":
        print("Wear sunglasses")
    else:
        print("Just go outside")  # ✅ This runs (no match above)

#example
        score = 85

        if score >= 50:
            print("Pass")  # ✅ This runs first → "Pass"
        elif score >= 80:
            print("Distinction")  # ❌ Never runs — skipped!

        score = 80
        if score >= 80:
            print("Distinction")  # ✅ Runs correctly
        elif score >= 50:
            print("Pass")

i