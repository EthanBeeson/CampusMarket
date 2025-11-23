from app.db import SessionLocal
from app.crud.users import create_user
import json
import os

"""
Create a new user and register them as an admin by adding their email to `config/admins.json`.
Usage: python scripts/create_admin_user.py admin@charlotte.edu Password123!
"""

import sys

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_admin_user.py <email> <password>")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    db = SessionLocal()
    try:
        try:
            user = create_user(db, email, password)
            print(f"Created user: {user.email} (id={user.id})")
        except Exception as e:
            print(f"Could not create user: {e}")
            # attempt to continue and just add to admins if user exists
            user = db.query(__import__('app').crud.users.User if False else None).first()

        # add to admins config
        os.makedirs("config", exist_ok=True)
        admin_path = os.path.join("config", "admins.json")
        try:
            with open(admin_path, "r", encoding="utf-8") as fh:
                admins = json.load(fh)
        except Exception:
            admins = []

        if email.lower() not in [a.lower() for a in admins]:
            admins.append(email.lower())
            with open(admin_path, "w", encoding="utf-8") as fh:
                json.dump(admins, fh, indent=2)
            print(f"Added {email} to {admin_path}")
        else:
            print(f"{email} is already an admin")

    finally:
        db.close()
