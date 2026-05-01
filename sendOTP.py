import smtplib
from email.mime.text import MIMEText

import random

def generate_otp():
    return str(random.randint(100000, 999999))

def send_email_otp(email, otp):
    msg = MIMEText(f"Your OTP is {otp}")
    msg["Subject"] = "OTP Verification"
    msg["From"] = "kavpat1812@gmail.com"
    msg["To"] = email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login("kavpat1812@gmail.com", "jkjuycxfgbdktrtp")
        server.send_message(msg)

from datetime import datetime, timedelta

otp_store = {}

def save_otp(identifier, otp):
    otp_store[identifier] = {
        "otp": otp,
        "expires": datetime.utcnow() + timedelta(minutes=5)
    }

def verify_otp(identifier, user_otp):
    data = otp_store.get(identifier)
    if not data:
        return False
    
    if datetime.utcnow() > data["expires"]:
        return False

    return data["otp"] == user_otp

# otp=generate_otp()
# send_email_otp("kavya8140988260@gmail.com", otp)
# save_otp("kavya8140988260@gmail.com", otp)
# print(verify_otp("kavya8140988260@gmail.com", otp))





