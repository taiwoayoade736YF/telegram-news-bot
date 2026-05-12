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