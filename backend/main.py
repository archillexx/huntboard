from typing import Literal

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pwdlib import PasswordHash
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database import SessionLocal
from extraction import ExtractionFailed, extract_skills
from models import Job, JobSkill, ProfileSkill, Skill, User
from scoring import fit_score, most_missed_skills, normalise_skills

app = FastAPI()

# Let the React dev server (a different origin) read this API's responses.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PATCH", "PUT"],
    allow_headers=["Content-Type"],
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


def job_skill_names(db: Session, job_id: int | None = None) -> dict[int, list[str]]:
    """Skill names per job, from one JOIN of job_skills to skills (optionally for one job)."""
    query = select(JobSkill.job_id, Skill.name).join(Skill, JobSkill.skill_id == Skill.id)
    if job_id is not None:
        query = query.where(JobSkill.job_id == job_id)
    names: dict[int, list[str]] = {}
    for row_job_id, name in db.execute(query):
        names.setdefault(row_job_id, []).append(name)
    return names


def profile_skill_names(db: Session) -> list[str]:
    """My skill names, from a JOIN of profile_skills to skills."""
    query = select(Skill.name).join(ProfileSkill, ProfileSkill.skill_id == Skill.id)
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


@app.get("/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.scalars(select(Job).order_by(Job.id)).all()
    skills = job_skill_names(db)
    mine = profile_skill_names(db)
    return [job_to_api(job, skills.get(job.id, []), mine) for job in jobs]


@app.post("/jobs", status_code=201)
def create_job(job_in: JobIn, db: Session = Depends(get_db)):
    job = Job(
        company_name=job_in.companyName,
        job_role=job_in.jobRole,
        job_status=job_in.jobStatus,
        # A blank box arrives as "" after stripping; store it as NULL ("not pasted").
        job_description=job_in.jobDescription or None,
        resume_text=job_in.resumeText or None,
    )
    db.add(job)
    db.commit()  # the job is saved before the AI is called, so a failure can't lose it
    db.refresh(job)
    if job.job_description:
        run_extraction(db, job)
        db.refresh(job)
    skills = job_skill_names(db, job.id).get(job.id, [])
    return job_to_api(job, skills, profile_skill_names(db))


@app.patch("/jobs/{job_id}")
def update_job_status(job_id: int, update: JobStatusUpdate, db: Session = Depends(get_db)):
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.job_status = update.jobStatus
    db.commit()
    db.refresh(job)
    return job_to_api(job, job_skill_names(db, job_id).get(job_id, []), profile_skill_names(db))


@app.put("/jobs/{job_id}/skills")
def set_job_skills(job_id: int, skills_in: SkillsIn, db: Session = Depends(get_db)):
    """Replace a job's skills; the delete and the inserts commit together or not at all."""
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    names = replace_job_skills(db, job_id, skills_in.skills)
    db.commit()
    return job_to_api(job, names, profile_skill_names(db))


@app.post("/jobs/{job_id}/extract")
def retry_extraction(job_id: int, db: Session = Depends(get_db)):
    """The Retry button: run extraction again on a saved job's description."""
    job = db.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job.job_description:
        raise HTTPException(status_code=400, detail="This job has no description to read")
    run_extraction(db, job)
    db.refresh(job)
    skills = job_skill_names(db, job_id).get(job_id, [])
    return job_to_api(job, skills, profile_skill_names(db))


@app.get("/profile/skills")
def get_profile_skills(db: Session = Depends(get_db)):
    return {"skills": profile_skill_names(db)}


@app.put("/profile/skills")
def set_profile_skills(skills_in: SkillsIn, db: Session = Depends(get_db)):
    """Replace my skills, in one transaction like set_job_skills."""
    skills = get_or_create_skills(db, skills_in.skills)
    db.execute(delete(ProfileSkill))
    db.add_all(ProfileSkill(skill_id=s.id) for s in skills)
    db.commit()
    return {"skills": profile_skill_names(db)}


@app.get("/gaps")
def list_gaps(db: Session = Depends(get_db)):
    """My most-missed skills across all jobs, ranked by your most_missed_skills."""
    jobs = list(job_skill_names(db).values())
    ranked = most_missed_skills(jobs, profile_skill_names(db))
    return [{"skill": skill, "count": count} for skill, count in ranked]


# ---------- Accounts ----------

# Argon2 with sensible settings: the same hasher you tried in your 7.1 drill.
password_hasher = PasswordHash.recommended()


class SignupIn(BaseModel):
    """What a client sends to create an account."""

    email: EmailStr                       # Pydantic rejects anything that isn't a real email shape
    password: str = Field(min_length=8)   # a basic floor; the hash can't save a weak password


@app.post("/auth/signup", status_code=201)
def signup(signup_in: SignupIn, db: Session = Depends(get_db)):
    """Create an account. Stores only the Argon2 hash; the password itself is never saved."""
    email = signup_in.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, password_hash=password_hasher.hash(signup_in.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    # Never send the hash back: the client has no use for it.
    return {"userId": user.id, "email": user.email}
