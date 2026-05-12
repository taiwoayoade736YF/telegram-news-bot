little_yf = ('dish', 'file', 'hen', 'life')
for the_item in little_yf:
    print(the_item, "*", )


countdown = 10
while countdown > 0:  # Explicit condition (optional but clearer)
    print(countdown, end=", ")  # Print the number, not the string "countdown"
    countdown -= 1
print("blastoff!")  # Outside the loop → prints only once at the end

countdown = 5
while countdown > 0:          # Condition: "Is countdown greater than 0?"
    print(f"T-minus {countdown} seconds")
    countdown -= 2             # ← CRITICAL: Changes the condition!
print("🚀 LIFTOFF!")


# WHILE LOOP EXAMPLE
age = None
while age is None or age < 0 or age > 150:
    user_input = input("Enter your age (0-150): ")

    # Try to convert to integer
    try:
        age = int(user_input)
        if age < 0 or age > 150:
            print("❌ Invalid age! Must be between 0 and 150.")
    except ValueError:
        print("❌ Please enter a NUMBER!")


print(f"✅ Accepted age: {age}")


# MORE COMPLEX WHILE LOOP EXAMPLE
import random

secret_number = random.randint(1, 10)
print("🎮 Guess the number between 1 and 10!")

while True:  # Infinite loop (condition always True)
    guess = int(input("Your guess: "))

    if guess == secret_number:
        print("🎉 Correct! You win!")
        break  # ← IMMEDIATELY exits the loop

    elif guess < secret_number:
        print("🔼 Too low!")
    else:
        print("🔽 Too high!")

print("Thanks for playing!")
    break
