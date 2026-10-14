import os
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from codes import CodeRejected, check_code, issue_code, seconds_until_resend
from database import SessionLocal
from extraction import ExtractionFailed, extract_skills
from mailer import EmailNotSent, send_email
from models import Job, JobSkill, ProfileSkill, Skill, User
from scoring import fit_score, most_missed_skills, normalise_skills

app = FastAPI()

# Let the React dev server (a different origin) read this API's responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "PUT"],
    allow_headers=["Content-Type", "Authorization"],  # Authorization carries the login token
)

JobStatus = Literal["Considering", "Applied", "Replied", "Interview", "Rejected", "Ghosted"]


class JobStatusUpdate(BaseModel):
    """What a client sends to change a job's status."""

    jobStatus: JobStatus


class JobIn(BaseModel):
    """What a client must send to create a job."""

    model_config = ConfigDict(str_strip_whitespace=True)

    companyName: str = Field(min_length=1)
    jobRole: str = Field(min_length=1)
    jobStatus: JobStatus = "Applied"
    jobDescription: str | None = None
    resumeText: str | None = None


class SkillsIn(BaseModel):
    """A full list of skill names; it replaces whatever was saved before."""

    skills: list[str]


def get_db():
    """Give each request its own database session, and always close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Who is asking? ----------

# Argon2 with sensible settings: the same hasher you tried in your 7.1 drill.
password_hasher = PasswordHash.recommended()

# Signs every login token. Read from .env (loaded by database.py); the app refuses to start without it.
JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
TOKEN_LIFETIME = timedelta(hours=24)


def create_access_token(user_id: int) -> str:
    """A signed token saying "this is user <id>", valid for TOKEN_LIFETIME."""
    expires = datetime.now(timezone.utc) + TOKEN_LIFETIME
    claims = {"sub": str(user_id), "exp": expires}   # sub = who; exp = when it stops working
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)


# Reads "Authorization: Bearer <token>" from each request. tokenUrl tells /docs where
# its Authorize button should log in.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """The dependency every data route uses: a valid token in, the logged-in User out.

    Any failure stops the request here with 401, so the route itself never runs.
    """
    not_logged_in = HTTPException(
        status_code=401,
        detail="Not logged in",
        headers={"WWW-Authenticate": "Bearer"},   # tells the client which kind of login is expected
    )
    try:
        # Checks the signature AND the exp claim; a forged, expired or garbled token raises.
        claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        raise not_logged_in
    user = db.get(User, int(claims["sub"]))
    if user is None:   # a valid token for an account that has since been deleted
        raise not_logged_in
    return user


def job_skill_names(db: Session, user_id: int, job_id: int | None = None) -> dict[int, list[str]]:
    """Skill names per job for ONE user's jobs (optionally just one job).

    The extra JOIN to jobs is what keeps another user's job skills out of the result.
    """
    query = (
        select(JobSkill.job_id, Skill.name)
        .join(Skill, JobSkill.skill_id == Skill.id)
        .join(Job, JobSkill.job_id == Job.id)
        .where(Job.user_id == user_id)
    )
    if job_id is not None:
        query = query.where(JobSkill.job_id == job_id)
    names: dict[int, list[str]] = {}
    for row_job_id, name in db.execute(query):
        names.setdefault(row_job_id, []).append(name)
    return names


def profile_skill_names(db: Session, user_id: int) -> list[str]:
    """One user's skill names, from a JOIN of profile_skills to skills."""
    query = (
        select(Skill.name)
        .join(ProfileSkill, ProfileSkill.skill_id == Skill.id)
        .where(ProfileSkill.user_id == user_id)
    )
    return sorted(db.scalars(query))


def get_or_create_skills(db: Session, raw_names: list[str]) -> list[Skill]:
    """Find a skills row for each name, adding rows for names not seen before."""
    # Blank entries are dropped; cleaning and aliases are your normalise_skills from scoring.py.
    names = set(normalise_skills([n for n in raw_names if n.strip()]))
    found = {s.name: s for s in db.scalars(select(Skill).where(Skill.name.in_(names)))}
    for name in names - found.keys():
        found[name] = Skill(name=name)
        db.add(found[name])
    db.flush()  # sends the INSERTs now so new skills get ids, but doesn't commit yet
    return list(found.values())


def job_to_api(job: Job, job_skills: list[str], my_skills: list[str]) -> dict:
    """Turn a database row (snake_case columns) into the JSON shape React expects."""
    score, missing = fit_score(job_skills, my_skills)
    return {
        "jobId": job.id,
        "companyName": job.company_name,
        "jobRole": job.job_role,
        "jobStatus": job.job_status,
        "jobDescription": job.job_description,
        "resumeText": job.resume_text,
        "skills": sorted(job_skills),
        "fitScore": score,
        "missingSkills": missing,
        "extractionStatus": job.extraction_status,
    }


def replace_job_skills(db: Session, job_id: int, raw_names: list[str]) -> list[str]:
    """Swap a job's skill links for new ones. Doesn't commit: the caller decides when."""
    skills = get_or_create_skills(db, raw_names)
    db.execute(delete(JobSkill).where(JobSkill.job_id == job_id))
    db.add_all(JobSkill(job_id=job_id, skill_id=s.id) for s in skills)
    return [s.name for s in skills]


def run_extraction(db: Session, job: Job) -> None:
    """Fill a saved job's skills from its description with your extract_skills.

    Never raises for an AI failure: the job is already saved, so a failure is only
    recorded as extraction_status = "failed", which the card shows with a Retry button.
    """
    try:
        names = extract_skills(job.job_description)
    except ExtractionFailed:
        job.extraction_status = "failed"
        db.commit()
        return
    replace_job_skills(db, job.id, names)
    job.extraction_status = "done"
    db.commit()


def get_own_job(db: Session, job_id: int, user: User) -> Job:
    """Fetch a job only if it belongs to this user.

    Someone else's job gets the same 404 as a job that doesn't exist, so users can't
    probe which job ids are in use.
    """
    job = db.get(Job, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def job_response(db: Session, job: Job) -> dict:
    """job_to_api with the job's own skills and its owner's profile."""
    skills = job_skill_names(db, job.user_id, job.id).get(job.id, [])
    return job_to_api(job, skills, profile_skill_names(db, job.user_id))


@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    jobs = db.scalars(select(Job).where(Job.user_id == user.id).order_by(Job.id)).all()
    skills = job_skill_names(db, user.id)
    mine = profile_skill_names(db, user.id)
    return [job_to_api(job, skills.get(job.id, []), mine) for job in jobs]


@app.post("/jobs", status_code=201)
def create_job(job_in: JobIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = Job(
        company_name=job_in.companyName,
        job_role=job_in.jobRole,
        job_status=job_in.jobStatus,
        # A blank box arrives as "" after stripping; store it as NULL ("not pasted").
        job_description=job_in.jobDescription or None,
        resume_text=job_in.resumeText or None,
        user_id=user.id,   # the owner comes from the token, never from the request body
    )
    db.add(job)
    db.commit()  # the job is saved before the AI is called, so a failure can't lose it
    db.refresh(job)
    if job.job_description:
        run_extraction(db, job)
        db.refresh(job)
    return job_response(db, job)


@app.patch("/jobs/{job_id}")
def update_job_status(job_id: int, update: JobStatusUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    job = get_own_job(db, job_id, user)
    job.job_status = update.jobStatus
    db.commit()
    db.refresh(job)
    return job_response(db, job)


@app.put("/jobs/{job_id}/skills")
def set_job_skills(job_id: int, skills_in: SkillsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Replace a job's skills; the delete and the inserts commit together or not at all."""
    job = get_own_job(db, job_id, user)
    replace_job_skills(db, job_id, skills_in.skills)
    db.commit()
    return job_response(db, job)


@app.post("/jobs/{job_id}/extract")
def retry_extraction(job_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The Retry button: run extraction again on a saved job's description."""
    job = get_own_job(db, job_id, user)
    if not job.job_description:
        raise HTTPException(status_code=400, detail="This job has no description to read")
    run_extraction(db, job)
    db.refresh(job)
    return job_response(db, job)


@app.get("/profile/skills")
def get_profile_skills(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return {"skills": profile_skill_names(db, user.id)}


@app.put("/profile/skills")
def set_profile_skills(skills_in: SkillsIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Replace my skills, in one transaction like set_job_skills."""
    skills = get_or_create_skills(db, skills_in.skills)
    db.execute(delete(ProfileSkill).where(ProfileSkill.user_id == user.id))   # only MY rows
    db.add_all(ProfileSkill(user_id=user.id, skill_id=s.id) for s in skills)
    db.commit()
    return {"skills": profile_skill_names(db, user.id)}


@app.get("/gaps")
def list_gaps(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """My most-missed skills across all jobs, ranked by your most_missed_skills."""
    jobs = list(job_skill_names(db, user.id).values())
    ranked = most_missed_skills(jobs, profile_skill_names(db, user.id))
    return [{"skill": skill, "count": count} for skill, count in ranked]


# ---------- Accounts ----------

class SignupIn(BaseModel):
    """What a client sends to create an account."""

    email: EmailStr                       # Pydantic rejects anything that isn't a real email shape
    password: str = Field(min_length=8)   # a basic floor; the hash can't save a weak password


VERIFY_EMAIL = "verify_email"   # the purpose stored on verification codes


def send_verification_code(db: Session, user: User) -> None:
    """Make a code, save it, then email it. Saved first, so the code exists before anyone can type it."""
    code = issue_code(db, user, VERIFY_EMAIL)
    db.commit()
    send_email(
        user.email,
        "Your Huntboard verification code",
        f"Your code is {code}\n\nIt expires in 15 minutes. If you didn't sign up for Huntboard, ignore this email.",
    )


@app.post("/auth/signup", status_code=201)
def signup(signup_in: SignupIn, db: Session = Depends(get_db)):
    """Create an unverified account and email it a code. Stores only the Argon2 hash of the password."""
    email = signup_in.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, password_hash=password_hasher.hash(signup_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    try:
        send_verification_code(db, user)
    except EmailNotSent:
        # The account exists; the user can ask for the code again with Resend.
        raise HTTPException(status_code=502, detail="Account created, but we couldn't send the code. Try Resend.")
    # Never send the hash back: the client has no use for it. No token yet: verify first.
    return {"userId": user.id, "email": user.email, "verified": False}


class VerifyIn(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


@app.post("/auth/verify")
def verify_email(verify_in: VerifyIn, db: Session = Depends(get_db)):
    """Check the emailed code. On success the account is verified and you're logged in."""
    user = db.scalar(select(User).where(User.email == verify_in.email.strip().lower()))
    # Unknown email: same reply as a wrong code, so this can't be used to find accounts.
    if user is None:
        raise HTTPException(status_code=400, detail="That code isn't right.")
    if user.email_verified_at is not None:
        raise HTTPException(status_code=400, detail="This email is already verified. Log in instead.")
    try:
        check_code(db, user, VERIFY_EMAIL, verify_in.code)
    except CodeRejected as error:
        db.commit()   # save the failed attempt first, or the 5-try limit never sticks
        raise HTTPException(status_code=400, detail=str(error))
    user.email_verified_at = datetime.now(timezone.utc)
    db.commit()       # the code's used_at and the user's verification save together
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}


class ResendIn(BaseModel):
    email: EmailStr


@app.post("/auth/resend-code")
def resend_code(resend_in: ResendIn, db: Session = Depends(get_db)):
    """Email a fresh code. Always the same reply, so it can't be used to check which emails have accounts."""
    reply = {"detail": "If that account needs verifying, a new code is on its way."}
    user = db.scalar(select(User).where(User.email == resend_in.email.strip().lower()))
    if user is None or user.email_verified_at is not None:
        return reply
    # Inside the cooldown: quietly send nothing (the page also counts down before allowing Resend).
    if seconds_until_resend(db, user, VERIFY_EMAIL) > 0:
        return reply
    try:
        send_verification_code(db, user)
    except EmailNotSent:
        raise HTTPException(status_code=502, detail="We couldn't send the code. Try again in a minute.")
    return reply


@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Check email + password and hand back a signed token.

    Uses FastAPI's standard login form (fields "username" and "password"), so the
    Authorize button on /docs can log in too. Here "username" is your email.
    """
    email = form.username.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    # Same message whether the email or the password was wrong, so attackers can't
    # use this route to find out which emails have accounts.
    if user is None or not password_hasher.verify(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Wrong email or password")
    # Checked only after the password is right, so it reveals nothing to someone guessing.
    if user.email_verified_at is None:
        raise HTTPException(status_code=403, detail="Verify your email first")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}
