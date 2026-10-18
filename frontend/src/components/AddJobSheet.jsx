import { useEffect, useRef, useState } from 'react'
import { STATUSES } from '../statuses'

const fieldClass = "mt-1.5 w-full rounded-xl border border-outline bg-surface px-3 py-2.5 text-sm text-text placeholder:text-muted-2 focus:outline-2 focus:outline-primary disabled:opacity-60"
const labelClass = "text-sm font-bold text-text"

// A side sheet (full-screen on phones) holding the add-job form.
// onSave(newJob) is Dashboard's addJob: it resolves to true once the job is saved.
export const AddJobSheet = ({ onSave, onClose }) => {
    const dialogRef = useRef(null)
    const [companyName, setCompanyName] = useState("")
    const [jobRole, setJobRole] = useState("")
    const [location, setLocation] = useState("")
    const [salary, setSalary] = useState("")
    const [jobStatus, setJobStatus] = useState("Applied")
    const [jobDescription, setJobDescription] = useState("")
    const [resumeText, setResumeText] = useState("")
    const [saving, setSaving] = useState(false)   // true while the job (and its AI extraction) saves
    const [error, setError] = useState("")

    // showModal() also focuses the field marked autoFocus (Company). The check matters in dev: StrictMode runs effects twice.
    useEffect(() => {
        if (!dialogRef.current.open) dialogRef.current.showModal()
    }, [])

    const close = () => dialogRef.current.close()

    // Esc fires "cancel" first; while saving, ignore it so the form stays put until the server answers.
    const blockWhileSaving = (e) => {
        if (saving) e.preventDefault()
    }

    const submit = async (e) => {
        e.preventDefault()

        // Quick check for the user; the server's Pydantic model is the real one.
        if (!companyName.trim() || !jobRole.trim()) return setError("Company and role are required.")

        setError("")
        setSaving(true)
        try {
            const saved = await onSave({ companyName, jobRole, location, salary, jobStatus, jobDescription, resumeText })
            if (saved) close()
            else setError("Couldn't save this job. Check the fields and try again.")
        } catch {
            setError("Can't reach the server. Is the backend running?")
        } finally {
            setSaving(false)
        }
    }

    return (
        <dialog ref={dialogRef} onClose={onClose} onCancel={blockWhileSaving} aria-labelledby="add-job-title"
            className="m-0 ml-auto h-dvh max-h-none w-full max-w-none bg-surface p-0 text-text backdrop:bg-black/50 sm:max-w-[460px] sm:rounded-l-[28px] motion-safe:transition-transform motion-safe:duration-200 motion-safe:starting:translate-x-full">
            <form className="flex h-full flex-col" onSubmit={submit}>
                <div className="flex items-center justify-between border-b border-border px-6 py-4">
                    <h2 id="add-job-title" className="text-xl font-extrabold">Add job</h2>
                    <button type="button" onClick={close} disabled={saving} aria-label="Close"
                        className="flex h-11 w-11 items-center justify-center rounded-full text-muted hover:bg-surface-variant focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                            <path d="M6 6l12 12M18 6L6 18" />
                        </svg>
                    </button>
                </div>

                {/* fieldset disabled = every field inside is disabled while saving */}
                <fieldset disabled={saving} className="flex-1 space-y-4 overflow-y-auto px-6 py-5">
                    <div>
                        <label htmlFor="add-company" className={labelClass}>Company</label>
                        <input id="add-company" autoFocus className={fieldClass} type="text" value={companyName} onChange={(e) => setCompanyName(e.target.value)} />
                    </div>
                    <div>
                        <label htmlFor="add-role" className={labelClass}>Role</label>
                        <input id="add-role" className={fieldClass} type="text" value={jobRole} onChange={(e) => setJobRole(e.target.value)} />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                        <div>
                            <label htmlFor="add-location" className={labelClass}>Location</label>
                            <input id="add-location" className={fieldClass} type="text" placeholder="e.g. Sydney, NSW" value={location} onChange={(e) => setLocation(e.target.value)} />
                        </div>
                        <div>
                            <label htmlFor="add-salary" className={labelClass}>Salary</label>
                            <input id="add-salary" className={fieldClass} type="text" placeholder="If the ad states one" value={salary} onChange={(e) => setSalary(e.target.value)} />
                        </div>
                    </div>
                    <div>
                        <label htmlFor="add-status" className={labelClass}>Status</label>
                        <select id="add-status" className={fieldClass} value={jobStatus} onChange={(e) => setJobStatus(e.target.value)}>
                            {STATUSES.map((status) => <option key={status}>{status}</option>)}
                        </select>
                    </div>
                    <div>
                        <label htmlFor="add-description" className={labelClass}>Job description</label>
                        <textarea id="add-description" className={`${fieldClass} h-36`} value={jobDescription} placeholder="Paste the job description" aria-describedby="add-description-hint" onChange={(e) => setJobDescription(e.target.value)} />
                        <p id="add-description-hint" className="mt-1.5 text-xs text-muted-2">Skills are extracted automatically.</p>
                    </div>
                    <div>
                        <label htmlFor="add-resume" className={labelClass}>Resume sent</label>
                        <textarea id="add-resume" className={`${fieldClass} h-28`} value={resumeText} placeholder="Paste the resume you sent (optional)" onChange={(e) => setResumeText(e.target.value)} />
                    </div>
                    {error && <p className="rounded-xl bg-missing px-3.5 py-2.5 text-sm font-bold text-on-missing" role="alert">{error}</p>}
                </fieldset>

                <div className="flex justify-end gap-2 border-t border-border px-6 py-4">
                    <button type="button" onClick={close} disabled={saving}
                        className="min-h-11 rounded-full px-5 text-sm font-bold text-primary hover:bg-surface-variant focus-visible:outline-2 focus-visible:outline-primary disabled:opacity-50">
                        Cancel
                    </button>
                    <button disabled={saving}
                        className="min-h-11 rounded-full bg-primary px-5 text-sm font-bold text-on-primary hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60">
                        {saving ? "Saving… reading the description" : "Save"}
                    </button>
                </div>
            </form>
        </dialog>
    )
}
