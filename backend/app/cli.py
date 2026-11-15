"""Command-line admin tasks. Run from the backend/ folder with the virtualenv active:

    python -m app.cli create-owner --email you@example.com --name "Your Name"
    python -m app.cli set-password --email someone@example.com

Both use DATABASE_URL from backend/.env, so they work against the deployed Neon database
from your laptop. These are the only ways to create the owner or recover the owner's password.
"""
import argparse
import getpass
import sys

from app.core.security import hash_password, normalize_email, password_problem
from app.migrate import run_migrations
from app.models.database import SessionLocal
from app.models.entities import ROLE_OWNER, STATUS_ACTIVE, User
from app.services.accounts import audit, revoke_sessions


def _ask_password() -> str:
    while True:
        password = getpass.getpass("Password: ")
        problem = password_problem(password)
        if problem:
            print(problem)
            continue
        if getpass.getpass("Repeat password: ") != password:
            print("Passwords don't match, try again.")
            continue
        return password


def create_owner(email: str, name: str) -> int:
    email = normalize_email(email)
    with SessionLocal() as db:
        owner = db.query(User).filter_by(role=ROLE_OWNER).first()
        if owner is not None:
            print(f"An owner already exists ({owner.email}). There can only be one owner; "
                  "use 'Transfer ownership' in the admin portal instead.")
            return 1
        user = db.query(User).filter_by(email=email).first()
        if user is not None:
            user.role = ROLE_OWNER
            user.status = STATUS_ACTIVE
            print(f"Existing account {email} is now the owner (password unchanged).")
        else:
            user = User(email=email, name=name.strip() or "Owner",
                        password_hash=hash_password(_ask_password()), role=ROLE_OWNER)
            db.add(user)
            db.flush()
            print(f"Owner account created for {email}.")
        audit(db, None, "owner.created", target=user)
        db.commit()
    return 0


def set_password(email: str) -> int:
    email = normalize_email(email)
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=email).first()
        if user is None:
            print(f"No account found for {email}.")
            return 1
        user.password_hash = hash_password(_ask_password())
        user.failed_logins = 0
        user.locked_until = None
        revoke_sessions(db, user.id)
        audit(db, None, "reset.completed", target=user, details={"via": "cli"})
        db.commit()
        print(f"Password updated for {email}. All their sessions were signed out.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli", description="NutriLens admin tasks")
    sub = parser.add_subparsers(dest="command", required=True)
    owner = sub.add_parser("create-owner", help="Create the single owner account")
    owner.add_argument("--email", required=True)
    owner.add_argument("--name", default="Owner")
    reset = sub.add_parser("set-password", help="Set a new password for any account")
    reset.add_argument("--email", required=True)
    args = parser.parse_args(argv)

    run_migrations()
    if args.command == "create-owner":
        return create_owner(args.email, args.name)
    return set_password(args.email)


if __name__ == "__main__":
    sys.exit(main())
