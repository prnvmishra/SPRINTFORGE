"""Remove accounts created by automated verification runs during development.

Browser-driven verification created real signup rows (e.g. "Editor Regression",
"UX Check"), which then appeared on the leaderboard alongside genuine users.
This script identifies those artifacts by name/email pattern and deletes them.

Emails are always masked in output. Nothing is deleted without --apply.

    python scripts/cleanup_test_accounts.py           # dry run, shows what matches
    python scripts/cleanup_test_accounts.py --apply   # perform the deletion
"""

from __future__ import annotations

import argparse
import sys

from sqlalchemy import func, or_, select

from app.core.database import SessionLocal
from app.models.entities import User

# Throwaway domains the verification agents signed up under. No genuine learner
# uses these, so a domain match is enough on its own.
ARTIFACT_DOMAINS = ["@sf.dev", "@sprintforge.dev", "@sprintforge.test", "@example.com"]

# Display names and email fragments used by the automated verification agents.
ARTIFACT_PATTERNS = [
    "neon check",
    "debug user",
    "editor regression",
    "mentor check",
    "ux check",
    "design check",
    "test user",
    "playwright",
    "sprintforge.test",
    "verify@",
]


def mask(email: str) -> str:
    local, _, domain = email.partition("@")
    return f"{local[:2]}***@{domain}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="actually delete the matches")
    parser.add_argument("--list", action="store_true", help="list every account, then exit")
    parser.add_argument(
        "--delete-email",
        action="append",
        default=[],
        metavar="EMAIL",
        help="delete one specific account by exact email (repeatable, needs --apply)",
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(User)) or 0

        if args.list:
            everyone = session.scalars(select(User).order_by(User.created_at)).all()
            print(f"accounts total: {total}\n")
            for user in everyone:
                print(
                    f"  {user.created_at:%Y-%m-%d %H:%M}  {user.name[:22]:<22} "
                    f"{mask(user.email):<28} onboarded={user.is_onboarded}"
                )
            return 0

        if args.delete_email:
            targets = session.scalars(
                select(User).where(User.email.in_(args.delete_email))
            ).all()
            print(f"matched {len(targets)} of {len(args.delete_email)} requested emails")
            for user in targets:
                print(f"  {user.name[:22]:<22} {mask(user.email)}")
            if not args.apply:
                print("\nDry run. Re-run with --apply to delete.")
                return 0
            for user in targets:
                session.delete(user)
            session.commit()
            remaining = session.scalar(select(func.count()).select_from(User)) or 0
            print(f"\nDeleted {len(targets)} accounts. Remaining: {remaining}")
            return 0

        conditions = [func.lower(User.name).like(f"%{p}%") for p in ARTIFACT_PATTERNS]
        conditions += [func.lower(User.email).like(f"%{p}%") for p in ARTIFACT_PATTERNS]
        conditions += [func.lower(User.email).like(f"%{d}") for d in ARTIFACT_DOMAINS]
        matches = session.scalars(
            select(User).where(or_(*conditions)).order_by(User.created_at)
        ).all()

        print(f"accounts total:      {total}")
        print(f"artifact matches:    {len(matches)}")
        print(f"would remain:        {total - len(matches)}")
        print()
        for user in matches:
            print(f"  {user.created_at:%Y-%m-%d %H:%M}  {user.name[:22]:<22} {mask(user.email)}")

        if not matches:
            print("\nNothing to clean up.")
            return 0

        if not args.apply:
            print("\nDry run. Re-run with --apply to delete these accounts.")
            return 0

        # ORM-level delete so relationship cascades and FK ON DELETE CASCADE both apply.
        for user in matches:
            session.delete(user)
        session.commit()

        remaining = session.scalar(select(func.count()).select_from(User)) or 0
        print(f"\nDeleted {len(matches)} accounts. Remaining: {remaining}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
