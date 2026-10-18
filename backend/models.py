from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Job(Base):
    """One job application: a row in the jobs table."""

    __tablename__ = "jobs"
    # The database itself rejects any status outside the six the API allows.
    __table_args__ = (
        CheckConstraint(
            "job_status IN ('Considering', 'Applied', 'Replied', 'Interview', 'Rejected', 'Ghosted')",
            name="job_status_allowed",
        ),
        # The same posting can't be saved twice by the same user. NULLs don't clash in Postgres,
        # so jobs added by hand (no URL) are unaffected; two different users can save the same URL.
        UniqueConstraint("user_id", "job_url", name="jobs_user_job_url_unique"),
    )  

    id: Mapped[int] = mapped_column(primary_key=True)
    company_name: Mapped[str]
    job_role: Mapped[str]
    job_status: Mapped[str] = mapped_column(server_default="Applied")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Pasted text, so they can be long; optional, since jobs can be saved before pasting.
    job_description: Mapped[str | None] = mapped_column(Text)
    resume_text: Mapped[str | None] = mapped_column(Text)
    # Set by the server, never by the client: "none" (no description to read),
    # "done" (skills extracted) or "failed" (AI gave up; the card offers Retry).
    extraction_status: Mapped[str] = mapped_column(server_default="none")
    # Who owns this job. Every query filters on it, so users only ever see their own jobs.
    # index=True: "all jobs WHERE user_id = ?" runs on every request, so look it up fast.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # Where the posting lives (set when saved from the browser extension). Optional for hand-added jobs.
    job_url: Mapped[str | None] = mapped_column(Text)
    # e.g. "Brisbane, QLD". Optional: hand-added jobs and some postings don't say.
    location: Mapped[str | None]
    # As the ad states it ("AUD 79,000–80,000 per year", "$90k + super"). Text, not numbers:
    # ads write pay in too many shapes to parse reliably, and showing it is all we need for now.
    salary: Mapped[str | None]


class Skill(Base):
    """One distinct skill name, stored once and shared by jobs and my profile."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)


class JobSkill(Base):
    """Join table: one row = 'this job requires this skill'."""

    __tablename__ = "job_skills"

    # Two-column primary key, so the same job-skill pair can't be stored twice.
    # CASCADE: deleting a job (or skill) deletes its links too.
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )


class ProfileSkill(Base):
    """One row = 'this user has this skill' (a users <-> skills join table)."""

    __tablename__ = "profile_skills"

    # Two-column primary key: each user can list a given skill once.
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )


class User(Base):
    """One account. Stores a password hash, never the password itself."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Saved lowercased and trimmed, so "Ashwin@Gmail.com" and "ashwin@gmail.com" are one account.
    email: Mapped[str] = mapped_column(unique=True)
    # The full "$argon2id$..." string from pwdlib: algorithm, settings, salt and hash.
    password_hash: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # When the email was proven real by entering a code; NULL = not verified yet, so login is refused.
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When the password last changed (or was reset). Tokens issued before this are refused,
    # which is how changing your password logs out every other session.
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OneTimeCode(Base):
    """A 6-digit code we emailed, e.g. to verify an email address. Stored hashed, like a password."""

    __tablename__ = "one_time_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Deleting a user deletes their codes too.
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # What the code is for: "verify_email" now, "reset_password" in 7b.5. One table, two uses.
    purpose: Mapped[str]
    code_hash: Mapped[str]
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # Wrong guesses so far; the code stops working after a few, so it can't be guessed.
    attempts: Mapped[int] = mapped_column(server_default="0")
    # Set when the code is used, so the same code can't be used twice.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
