#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import create_app
from app.models.user import User


def main() -> int:
    app = create_app()
    with app.app_context():
        uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        print(f"SQLALCHEMY_DATABASE_URI: {uri}")
        users = User.query.all()
        print(f"User count: {len(users)}")
        for u in users:
            print(f"- id={u.id} email={u.email} is_admin={u.is_admin} password_hash={repr(u.password_hash)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


