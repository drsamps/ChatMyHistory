#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.extensions import db
from app.models.user import User


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/set_user_password.py <email> <new_password>")
        return 2

    email = sys.argv[1].strip().lower()
    new_password = sys.argv[2]

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User not found: {email}")
            return 1
        user.set_password(new_password)
        db.session.commit()
        print(f"Password updated for {email}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


