import { useEffect, useState } from 'react'
import { makeApi } from '../api'
import { AddJobSheet } from '../components/AddJobSheet'
import { GapList } from '../components/GapList'
import { Header } from '../components/Header'
import { JobCard } from '../components/JobCard'
import { JobDetailDialog } from '../components/JobDetailDialog'
import { SkeletonCard, SkeletonLines } from '../components/Skeleton'
import { SkillsEditor } from '../components/SkillsEditor'
import { STATUSES } from '../statuses'

export const Dashboard = ({ token, onLogout }) => {

    const api = makeApi(token, onLogout)

    const [jobs, setJobs] = useState(null)            // null = still loading
    const [jobsError, setJobsError] = useState(false)
    const [mySkills, setMySkills] = useState(null)  // null = not loaded yet
    const [gaps, setGaps] = useState(null)            // null = still loading
    const [gapsError, setGapsError] = useState(false)
    const [statusFilter, setStatusFilter] = useState("All")
    const [search, setSearch] = useState("")
    const [openJobId, setOpenJobId] = useState(null)   // the job whose detail dialog is open
    const [addOpen, setAddOpen] = useState(false)      // is the add-job sheet open?

    // A 401 is handled by api() (it logs out), so only other failures count as errors here.
    // fetch throws when the server can't be reached at all, hence the catch.
    const loadJobs = async () => {
        setJobsError(false)
        try {
            const response = await api(`/jobs`)
            if (!response.ok) return setJobsError(response.status !== 401)
            setJobs(await response.json())
        } catch {
            setJobsError(true)
        }
    }

    // Gaps depend on everyone's skills, so this reloads after any skills save.
    const loadGaps = async () => {
        setGapsError(false)
        try {
            const response = await api(`/gaps`)
            if (!response.ok) return setGapsError(response.status !== 401)
            setGaps(await response.json())
        } catch {
            setGapsError(true)
        }
    }

    // Load the jobs and my skills from the server once, when the dashboard first appears.
    useEffect(() => {
        const loadMySkills = async () => {
            try {
                const response = await api(`/profile/skills`)
                if (!response.ok) return
                setMySkills((await response.json()).skills)
            } catch {
                // the jobs error state already tells you the server is unreachable
            }
        }
        loadJobs()
        loadMySkills()
        loadGaps()
    }, [])

    // Save a new job from the add-job sheet. Resolves to true once saved, so the sheet knows to close.
    // The sheet handles the "saving…" state and the quick empty-field check.
    const addJob = async (newJob) => {
        const response = await api(`/jobs`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newJob),
        })
        if (!response.ok) return false

        const savedJob = await response.json()
        setJobs((jobs) => [...(jobs ?? []), savedJob])
        loadGaps()
        return true
    }

    // The Retry button: ask the server to run extraction again, then swap in the updated job.
    const retryExtraction = async (jobId) => {
        const response = await api(`/jobs/${jobId}/extract`, { method: "POST" })
        if (!response.ok) return

        const savedJob = await response.json()
        setJobs((jobs) => jobs.map((job) => job.jobId === jobId ? savedJob : job))
        loadGaps()
    }
    // Save the new status on the server first; only update the card once it's saved.
    const changeStatus = async (jobId, newStatus) => {
        const response = await api(`/jobs/${jobId}`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ jobStatus: newStatus }),
        })
        if (!response.ok) return

        const savedJob = await response.json()
        setJobs((jobs) => jobs.map((job) => job.jobId === jobId ? savedJob : job))
    }

    // Same pattern for a job's skills: the server sends back the job with its new score.
    const saveJobSkills = async (jobId, skillList) => {
        const response = await api(`/jobs/${jobId}/skills`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skills: skillList }),
        })
        if (!response.ok) return

        const savedJob = await response.json()
        setJobs((jobs) => jobs.map((job) => job.jobId === jobId ? savedJob : job))
        loadGaps()
    }

    // My skills change every job's score, so reload all the jobs after saving.
    const saveMySkills = async (skillList) => {
        const response = await api(`/profile/skills`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ skills: skillList }),
        })
        if (!response.ok) return

        setMySkills((await response.json()).skills)
        loadJobs()
        loadGaps()
    }

    const retryLoading = () => {
        setJobs(null)
        setGaps(null)
        loadJobs()
        loadGaps()
    }

    const openAddJob = () => setAddOpen(true)

    // Display-only numbers worked out from the jobs already loaded (no new API calls).
    const email = localStorage.getItem("email") ?? ""
    const scored = (jobs ?? []).filter((job) => job.fitScore !== null)
    const interviews = (jobs ?? []).filter((job) => job.jobStatus === "Interview").length
    const averageFit = scored.length ? Math.round(scored.reduce((sum, job) => sum + job.fitScore, 0) / scored.length) : null

    // Filter + search happen in the browser, on the jobs already loaded.
    const query = search.trim().toLowerCase()
    const visibleJobs = (jobs ?? []).filter((job) =>
        (statusFilter === "All" || job.jobStatus === statusFilter) &&
        (!query || job.companyName.toLowerCase().includes(query) || job.jobRole.toLowerCase().includes(query))
    )
    // Looked up from jobs each render, so the dialog shows fresh data after a skills save.
    const openJob = (jobs ?? []).find((job) => job.jobId === openJobId)
    const countFor = (status) => (jobs ?? []).filter((job) => status === "All" || job.jobStatus === status).length

    return (
        <div className="min-h-screen bg-background">
            <Header>
                {email && (
                    <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-container text-sm font-extrabold text-on-primary-container" title={email} aria-label={`Signed in as ${email}`} role="img">
                        {email[0].toUpperCase()}
                    </span>
                )}
                <button className="min-h-11 rounded-full border border-outline px-4 text-sm font-bold text-text hover:bg-surface-variant focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary" onClick={onLogout}>
                    Log out
                </button>
            </Header>

            <main className="page-width py-8">
                <div className="flex flex-wrap items-end justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-extrabold text-text">Your applications</h1>
                        {jobs && (
                            <p className="mt-1 text-muted">
                                {jobs.length} {jobs.length === 1 ? "application" : "applications"} · {interviews} {interviews === 1 ? "interview" : "interviews"}
                                {averageFit !== null && <> · {averageFit}% average fit</>}
                            </p>
                        )}
                    </div>
                    <button className="inline-flex min-h-11 items-center gap-2 rounded-full bg-primary px-5 text-sm font-bold text-on-primary hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary" onClick={openAddJob}>
                        <span aria-hidden="true" className="text-lg leading-none">+</span> Add job
                    </button>
                </div>

                <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
                    <div className="min-w-0">
                        {/* Search on its own row, then the status chips: they wrap on wider screens and scroll sideways on phones. */}
                        <div className="flex flex-col gap-3">
                            <label htmlFor="search" className="sr-only">Search by company or role</label>
                            <input id="search" type="search" placeholder="Search company or role" value={search} onChange={(e) => setSearch(e.target.value)}
                                className="min-h-11 w-full rounded-full border border-outline bg-surface px-4 text-sm text-text placeholder:text-muted-2 focus:outline-2 focus:outline-primary sm:max-w-sm" />
                            <div className="-mx-1 flex gap-2 overflow-x-auto px-1 pb-1 sm:flex-wrap sm:overflow-visible" role="group" aria-label="Filter by status">
                                {["All", ...STATUSES].map((status) => (
                                    <button key={status} aria-pressed={statusFilter === status} onClick={() => setStatusFilter(status)}
                                        className={`min-h-11 shrink-0 rounded-full px-4 text-sm font-bold focus-visible:outline-2 focus-visible:outline-primary ${statusFilter === status ? "bg-primary-container text-on-primary-container" : "border border-outline text-muted hover:bg-surface-variant"}`}>
                                        {status}{jobs && <span className="ml-1.5 opacity-70">{countFor(status)}</span>}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="mt-5">
                            {jobsError ? (
                                <div className="rounded-[20px] border border-border bg-surface p-8 text-center">
                                    <p className="font-extrabold text-text">Couldn't load your applications.</p>
                                    <p className="mt-1 text-sm text-muted">Check that the backend is running, then try again.</p>
                                    <button className="mt-4 min-h-11 rounded-full bg-primary px-5 text-sm font-bold text-on-primary hover:opacity-90" onClick={retryLoading}>Try again</button>
                                </div>
                            ) : jobs === null ? (
                                <div className="grid grid-cols-[repeat(auto-fill,minmax(min(300px,100%),1fr))] gap-4" aria-busy="true" aria-label="Loading applications">
                                    {Array.from({ length: 6 }, (_, i) => <SkeletonCard key={i} />)}
                                </div>
                            ) : jobs.length === 0 ? (
                                <div className="rounded-[20px] border border-dashed border-outline p-10 text-center">
                                    <p className="text-lg font-extrabold text-text">No applications yet</p>
                                    <p className="mt-1 text-sm text-muted">Save a job and Huntboard will score your fit.</p>
                                    <button className="mt-5 min-h-11 rounded-full bg-primary px-5 text-sm font-bold text-on-primary hover:opacity-90" onClick={openAddJob}>Add your first job</button>
                                </div>
                            ) : visibleJobs.length === 0 ? (
                                <p className="rounded-[20px] border border-dashed border-outline p-8 text-center text-sm text-muted">No applications match this filter.</p>
                            ) : (
                                <div className="grid grid-cols-[repeat(auto-fill,minmax(min(300px,100%),1fr))] gap-4">
                                    {visibleJobs.map((job) => (
                                        <JobCard key={job.jobId} job={job} onStatusChange={changeStatus} onRetry={retryExtraction} onOpen={setOpenJobId} />
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Side panel: my skills (they drive every fit score) and my most-missed skills. */}
                    <aside className="space-y-4">
                        <section className="rounded-[20px] border border-border bg-surface p-5 shadow-sm dark:shadow-none">
                            <h2 className="mb-3 font-extrabold text-text">My skills</h2>
                            {mySkills !== null
                                ? <SkillsEditor id="my-skills" label="Skills you have" initialSkills={mySkills} placeholder="Your skills, comma-separated" onSave={saveMySkills} />
                                : <SkeletonLines count={2} />}
                        </section>
                        <GapList gaps={gaps} error={gapsError} onRetry={retryLoading} />
                    </aside>
                </div>

            </main>

            {addOpen && <AddJobSheet onSave={addJob} onClose={() => setAddOpen(false)} />}
            {openJob && <JobDetailDialog job={openJob} onClose={() => setOpenJobId(null)} onSkillsSave={saveJobSkills} />}
        </div>
    )
}
