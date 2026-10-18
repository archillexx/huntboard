import { useState } from 'react'
import { FitScore } from './FitScore'
import { SkillChip } from './SkillChip'
import { StatusChip } from './StatusChip'
import { STATUSES } from '../statuses'

// One job in the grid: role, company, status, fit score, a peek at missing skills.
// The role title is a button whose ::after stretches over the whole card, so clicking anywhere opens the details;
// the Retry button and status picker sit above it (relative z-10) so they still work on their own.
export const JobCard = ({ job, onStatusChange, onRetry, onOpen }) => {
    const [retrying, setRetrying] = useState(false)

    // Keep the button disabled until the server answers, so one click = one AI call.
    const retry = async () => {
        setRetrying(true)
        try {
            await onRetry(job.jobId)
        } finally {
            setRetrying(false)
        }
    }

    const shownMissing = job.missingSkills.slice(0, 3)
    const moreMissing = job.missingSkills.length - shownMissing.length

    return (
        <article className="relative flex flex-col rounded-[20px] border border-border bg-surface p-5 shadow-sm transition hover:border-outline has-[h3_button:focus-visible]:outline-2 has-[h3_button:focus-visible]:outline-primary dark:shadow-none">
            <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                    <h3 className="truncate text-lg font-extrabold text-text">
                        <button className="text-left after:absolute after:inset-0 after:rounded-[20px] focus:outline-none" onClick={() => onOpen(job.jobId)}>{job.jobRole}</button>
                    </h3>
                    <p className="truncate text-sm text-muted-2">{job.companyName}{job.location && ` · ${job.location}`}</p>
                    {job.salary && <p className="truncate text-xs font-bold text-muted">{job.salary}</p>}
                </div>
                <StatusChip status={job.jobStatus} />
            </div>

            <div className="mt-5">
                <FitScore score={job.fitScore} />
            </div>

            {shownMissing.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-1.5">
                    {shownMissing.map((skill) => <SkillChip key={skill} name={skill} missing />)}
                    {moreMissing > 0 && <span className="self-center text-xs font-bold text-muted-2">+{moreMissing} more</span>}
                </div>
            )}

            {job.extractionStatus === "failed" && (
                <div className="relative z-10 mt-4 flex items-center justify-between gap-2 rounded-xl bg-missing px-3 py-2">
                    <p className="text-sm font-bold text-on-missing">Skill extraction failed</p>
                    <button className="min-h-11 rounded-full px-4 text-sm font-bold text-on-missing hover:bg-on-missing/10 focus-visible:outline-2 focus-visible:outline-on-missing disabled:opacity-50" disabled={retrying} onClick={retry}>
                        {retrying ? "Retrying…" : "Retry"}
                    </button>
                </div>
            )}

            {/* mt-auto pushes the status picker to the bottom, so cards in a row line up. */}
            <div className="relative z-10 mt-auto pt-5">
                <label htmlFor={`status-${job.jobId}`} className="sr-only">Status for {job.jobRole} at {job.companyName}</label>
                <select id={`status-${job.jobId}`} className="min-h-11 w-full rounded-xl border border-outline bg-surface px-3 text-sm font-bold text-text focus:outline-2 focus:outline-primary"
                    value={job.jobStatus} onChange={(e) => onStatusChange(job.jobId, e.target.value)}>
                    {STATUSES.map((status) => <option key={status}>{status}</option>)}
                </select>
            </div>
        </article>
    )
}
