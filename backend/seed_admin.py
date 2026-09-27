"""Create the first admin account (there is no other way to get one).
Run from the backend/ folder:
    python seed_admin.py 0712345678 "Your Name"
It asks for the password so it never appears in your terminal history."""
import getpass
import sys

from sqlalchemy import select

import app.models  # noqa: F401
from app.core.phone import normalize_phone
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.user import Role, User


def main():
    if len(sys.argv) != 3:
        sys.exit('Usage: python seed_admin.py <phone> "<full name>"')
    try:
        phone = normalize_phone(sys.argv[1])
    except ValueError as exc:
        sys.exit(str(exc))

    password = getpass.getpass("Admin password (min 8 characters): ")
    if len(password) < 8:
        sys.exit("Password is too short.")

    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.phone == phone)):
            sys.exit("A user with this phone already exists.")
        db.add(User(full_name=sys.argv[2], phone=phone, password_hash=hash_password(password), role=Role.ADMIN))
        db.commit()
    print("Admin created. Start the server and log in at /docs.")


if __name__ == "__main__":
    main()
