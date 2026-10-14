"""One-time codes: 6-digit codes we email to prove someone owns an address.

Used for email verification now, and for password resets in 7b.5 (the `purpose` keeps them apart).
These functions change rows but never commit: the route decides when to save.
"""

import math
import secrets
from datetime import datetime, timedelta, timezone

from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from models import OneTimeCode, User

CODE_LIFETIME = timedelta(minutes=15)
MAX_ATTEMPTS = 5                          # wrong guesses allowed before the code dies
RESEND_COOLDOWN = timedelta(seconds=60)   # minimum gap between codes, so nobody can flood an inbox

code_hasher = PasswordHash.recommended()  # the same Argon2 as passwords: slow on purpose


class CodeRejected(Exception):
    """The code didn't work. The message is safe to show the user."""


def issue_code(db: Session, user: User, purpose: str) -> str:
    """Make a new code, store only its hash, and return the plain code (to email, never to log)."""
    # secrets (not random) is made for security: its numbers can't be predicted.
    # :06d pads with zeros, so 4821 becomes "004821" and every code is 6 digits.
    code = f"{secrets.randbelow(1_000_000):06d}"
    db.add(OneTimeCode(
        user_id=user.id,
        purpose=purpose,
        code_hash=code_hasher.hash(code),
        expires_at=datetime.now(timezone.utc) + CODE_LIFETIME,
    ))
    return code


def latest_code(db: Session, user: User, purpose: str) -> OneTimeCode | None:
    """The user's newest unused code for this purpose. Older ones are ignored, so Resend replaces them."""
    return db.scalars(
        select(OneTimeCode)
        .where(OneTimeCode.user_id == user.id, OneTimeCode.purpose == purpose, OneTimeCode.used_at.is_(None))
        .order_by(OneTimeCode.created_at.desc(), OneTimeCode.id.desc())
        .limit(1)
    ).first()


def check_code(db: Session, user: User, purpose: str, code: str) -> None:
    """Accept the code (and mark it used) or raise CodeRejected.

    A wrong guess adds 1 to attempts, so the caller must commit even when this raises.
    """
    row = latest_code(db, user, purpose)
    now = datetime.now(timezone.utc)

    if row is None:
        raise CodeRejected("There's no active code. Request a new one.")
    if row.expires_at <= now:
        raise CodeRejected("This code has expired. Request a new one.")
    if row.attempts >= MAX_ATTEMPTS:
        raise CodeRejected("Too many wrong tries. Request a new code.")
    if not code_hasher.verify(code.strip(), row.code_hash):
        row.attempts += 1
        raise CodeRejected("That code isn't right.")

    row.used_at = now   # one use only


def seconds_until_resend(db: Session, user: User, purpose: str) -> int:
    """0 if a new code may be sent now, else how many seconds to wait."""
    row = latest_code(db, user, purpose)
    if row is None:
        return 0
    wait = (row.created_at + RESEND_COOLDOWN - datetime.now(timezone.utc)).total_seconds()
    # Round partial seconds up (2.3s left -> "wait 3"), but nothing left means 0.
    return math.ceil(wait) if wait > 0 else 0
