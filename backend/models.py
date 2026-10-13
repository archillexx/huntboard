from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Text, func
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
    """One row = 'I have this skill'. Single user, so no user column."""

    __tablename__ = "profile_skills"

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
