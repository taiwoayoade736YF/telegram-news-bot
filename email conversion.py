#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Send daily calendar via email - Python 3 version
"""
import smtplib

my_address = 'taiwoayoade736@gmail.com'
headers = [
    'Subject: Daily calendar',
    'From: ' + my_address,
    'To: ' + my_address,
]

# Read calendar file safely using context manager
try:
    with open('my_calendar', 'r', encoding='utf-8') as f:
        entries = f.read()
except FileNotFoundError:
    entries = "No calendar entries found."

# Build the message (SMTP requires \r\n line endings)
msg = '\r\n'.join(headers) + '\r\n\r\n' + entries

# Send the email
try:
    # Replace 'mail' with your actual SMTP server (e.g., 'smtp.gmail.com', 'localhost')
    smtp = smtplib.SMTP('mail', port=25)

    # Optional: Enable TLS for security (uncomment if your server supports it)
    # smtp.starttls()
    # smtp.login(my_address, 'your_password')  # If authentication is required

    smtp.sendmail(my_address, [my_address], msg)
    print("Email sent successfully!")

except smtplib.SMTPException as e:
    print(f"Failed to send email: {e}")

finally:
    smtp.quit()  # Properly close the connection (Python 3 preferred over .close())