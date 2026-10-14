import { useEffect, useRef } from 'react'
import { FitScore } from './FitScore'
import { SkillChip } from './SkillChip'
import { SkillsEditor } from './SkillsEditor'
import { StatusChip } from './StatusChip'

// The full view of one job. Built on the browser's <dialog>: showModal() dims the page,
// keeps keyboard focus inside, and closes on Esc (which fires onClose).
export const JobDetailDialog = ({ job, onClose, onSkillsSave }) => {
    const dialogRef = useRef(null)

    // Open it once it's on the page. The check matters in dev: StrictMode runs effects twice.
    useEffect(() => {
        if (!dialogRef.current.open) dialogRef.current.showModal()
    }, [])

    // A click that lands on the dialog itself (not its content) is a click on the dimmed backdrop.
    const closeOnBackdrop = (e) => {
        if (e.target === dialogRef.current) dialogRef.current.close()
    }

    return (
        <dialog ref={dialogRef} onClose={onClose} onClick={closeOnBackdrop} aria-labelledby="job-detail-title"
            className="m-auto max-h-[90vh] w-[calc(100%-2rem)] max-w-2xl overflow-y-auto rounded-[28px] bg-surface p-0 text-text backdrop:bg-black/50">
            <div className="p-6 sm:p-8">
                <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                        <h2 id="job-detail-title" className="text-2xl font-extrabold">{job.jobRole}</h2>
                        <p className="text-muted-2">{job.companyName}</p>
                    </div>
                    <button onClick={() => dialogRef.current.close()} aria-label="Close"
                        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-muted hover:bg-surface-variant focus-visible:outline-2 focus-visible:outline-primary">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg>
                    </button>
                </div>

                <div className="mt-3"><StatusChip status={job.jobStatus} /></div>

                <div className="mt-6"><FitScore score={job.fitScore} /></div>

                <section className="mt-6">
                    <h3 className="text-sm font-bold">Skills this job asks for</h3>
                    {job.skills.length === 0 ? (
                        <p className="mt-2 text-sm text-muted-2">None yet. Add them below, or paste a description when you save a job.</p>
                    ) : (
                        <div className="mt-2 flex flex-wrap gap-1.5">
                            {job.skills.map((skill) => <SkillChip key={skill} name={skill} missing={job.missingSkills.includes(skill)} />)}
                        </div>
                    )}
                </section>

                <div className="mt-6">
                    {/* key: a new skills list remounts the editor, because its useState only reads initialSkills once */}
                    <SkillsEditor key={job.skills.join(",")} id={`job-skills-${job.jobId}`} label="Edit skills" initialSkills={job.skills}
                        placeholder="Required skills, comma-separated" onSave={(list) => onSkillsSave(job.jobId, list)} />
                </div>

                {job.jobDescription && (
                    <section className="mt-6">
                        <h3 className="text-sm font-bold">Job description</h3>
                        <p className="mt-2 max-h-64 overflow-y-auto whitespace-pre-line rounded-xl bg-surface-variant p-4 text-sm text-muted">{job.jobDescription}</p>
                    </section>
                )}

                {job.resumeText && (
                    <details className="mt-4 text-sm">
                        <summary className="min-h-11 cursor-pointer content-center font-bold text-primary">Resume sent</summary>
                        <p className="mt-2 max-h-64 overflow-y-auto whitespace-pre-line rounded-xl bg-surface-variant p-4 text-muted">{job.resumeText}</p>
                    </details>
                )}
            </div>
        </dialog>
    )
}
