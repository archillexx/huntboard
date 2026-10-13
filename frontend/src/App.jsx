import { useEffect, useState } from 'react'

// The API's address comes from an environment variable (see .env.development).
const API_URL = import.meta.env.VITE_API_URL

// A comma-separated text box for a list of skills, saved with one button.
const SkillsEditor = ({ initialSkills, placeholder, onSave }) => {
    const [text, setText] = useState(initialSkills.join(", "))

    const save = (e) => {
        e.preventDefault()
        onSave(text.split(","))
    }

    return (
        <form className="mt-2 flex gap-2" onSubmit={save}>
            <input className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm" type="text" value={text} placeholder={placeholder} onChange={(e) => setText(e.target.value)} />
            <button className="rounded-md bg-indigo-600 px-3 py-1 text-sm font-medium text-white hover:bg-indigo-700">Save</button>
        </form>
    )
}

const JobCard = ({ companyName, jobRole, jobStatus, jobId, jobDescription, resumeText, skills, fitScore, missingSkills, extractionStatus, onStatusChange, onSkillsSave, onRetry }) => {
    const [retrying, setRetrying] = useState(false)

    // Keep the button disabled until the server answers, so one click = one AI call.
    const retry = async () => {
        setRetrying(true)
        try {
            await onRetry(jobId)
        } finally {
            setRetrying(false)
        }
    }

    return (
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <h3 className="text-lg font-semibold text-gray-900">{companyName}</h3>
            <h5 className="text-sm text-gray-600">{jobRole}</h5>
            <h6 className="mt-2 text-xs font-medium uppercase tracking-wide text-indigo-600">{jobStatus}</h6>
            
            <select className="mt-2 w-full rounded-md border border-gray-300 px-2 py-1 text-sm" value={jobStatus} onChange={(e)=>onStatusChange(jobId,e.target.value)}>
                <option>Applied</option>
                <option>Rejected</option>
                <option>Considering</option>
                <option>Ghosted</option>
                <option>Replied</option>
                <option>Interview</option>
            </select>

            <div className="mt-3 text-sm">
                {fitScore === null ? (
                    <p className="text-gray-500">No skills listed yet</p>
                ) : (
                    <p className="font-medium text-gray-900">{Math.round(fitScore)}% fit</p>
                )}
                {missingSkills.length > 0 && (
                    <p className="text-red-600">Missing: {missingSkills.join(", ")}</p>
                )}
            </div>
            {extractionStatus === "failed" && (
                <div className="mt-2 flex items-center gap-2 text-sm">
                    <p className="text-red-600">Couldn't read the skills from the description.</p>
                    <button className="rounded-md border border-red-300 px-2 py-0.5 text-red-700 hover:bg-red-50 disabled:opacity-50" disabled={retrying} onClick={retry}>
                        {retrying ? "Retrying…" : "Retry"}
                    </button>
                </div>
            )}
            {/* key: a new skills list remounts the editor, because its useState only reads initialSkills once */}
            <SkillsEditor key={skills.join(",")} initialSkills={skills} placeholder="Required skills, comma-separated" onSave={(list) => onSkillsSave(jobId, list)} />

            {jobDescription && (
                <p className="mt-3 line-clamp-3 whitespace-pre-line text-sm text-gray-700">{jobDescription}</p>
            )}
            {resumeText && (
                <details className="mt-2 text-sm">
                    <summary className="cursor-pointer text-indigo-600">Resume sent</summary>
                    <p className="mt-1 whitespace-pre-line text-gray-700">{resumeText}</p>
                </details>
            )}
        </div>
    )
}




// My most-missed skills across all jobs, most-missed first.
const GapList = ({ gaps }) => {
    return (
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
            <h4 className="font-semibold text-gray-900">Most-missed skills</h4>
            {gaps.length === 0 ? (
                <p className="mt-2 text-sm text-gray-500">No gaps yet. Add skills to your jobs to see them here.</p>
            ) : (
                <ol className="mt-2 space-y-1 text-sm">
                    {gaps.map((gap) => (
                        <li key={gap.skill} className="flex justify-between">
                            <span className="text-gray-900">{gap.skill}</span>
                            <span className="text-gray-500">{gap.count} {gap.count === 1 ? "job" : "jobs"}</span>
                        </li>
                    ))}
                </ol>
            )}
        </div>
    )
}

const JobList = ({ token, onLogout }) => {

    // Every API call goes through here: it adds the token, and a 401 (expired or bad token) logs out.
    const api = async (path, options = {}) => {
        const response = await fetch(`${API_URL}${path}`, {
            ...options,
            headers: { ...options.headers, Authorization: `Bearer ${token}` },
        })
        if (response.status === 401) onLogout()
        return response
    }

    const [jobArray, setJobArray] = useState([])
    const [companyName, setCompanyName] = useState("")
    const [jobRole, setJobRole] = useState("")
    const [jobDescription, setJobDescription] = useState("")
    const [resumeText, setResumeText] = useState("")
    const [mySkills, setMySkills] = useState(null)  // null = not loaded yet
    const [saving, setSaving] = useState(false)       // true while a new job (and its AI extraction) is saving
    const [gaps, setGaps] = useState([])

    const loadJobs = async () => {
        const response = await api(`/jobs`)
        if (!response.ok) return
        setJobArray(await response.json())
    }

    // Gaps depend on everyone's skills, so this reloads after any skills save.
    const loadGaps = async () => {
        const response = await api(`/gaps`)
        if (!response.ok) return
        setGaps(await response.json())
    }

    // Load the jobs and my skills from the server once, when JobList first appears.
    useEffect(() => {
        const loadMySkills = async () => {
            const response = await api(`/profile/skills`)
            if (!response.ok) return
            setMySkills((await response.json()).skills)
        }
        loadJobs()
        loadMySkills()
        loadGaps()
    }, [])



    const addJob = async (e) => {
        e.preventDefault()

        // Quick check for the user; the server's Pydantic model is the real one.
        if (!companyName.trim() || !jobRole.trim()) return

        // Saving can take several seconds while the AI reads the description.
        setSaving(true)
        try {
            const response = await api(`/jobs`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ companyName, jobRole, jobDescription, resumeText }),
            })
            if (!response.ok) return

            const savedJob = await response.json()
            setJobArray((jobs) => [...jobs, savedJob])
            setCompanyName("")
            setJobRole("")
            setJobDescription("")
            setResumeText("")
            loadGaps()
        } finally {
            setSaving(false)   // runs on success, early return, or a failed fetch
        }
    }

    // The Retry button: ask the server to run extraction again, then swap in the updated job.
    const retryExtraction = async (jobId) => {
        const response = await api(`/jobs/${jobId}/extract`, { method: "POST" })
        if (!response.ok) return

        const savedJob = await response.json()
        setJobArray((jobs) => jobs.map((job) => job.jobId === jobId ? savedJob : job))
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
        setJobArray((jobs) => jobs.map((job) => job.jobId === jobId ? savedJob : job))
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
        setJobArray((jobs) => jobs.map((job) => job.jobId === jobId ? savedJob : job))
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



    return (
        <div className="space-y-4">

            <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
                <h4 className="font-semibold text-gray-900">My skills</h4>
                {mySkills !== null && (
                    <SkillsEditor initialSkills={mySkills} placeholder="Your skills, comma-separated" onSave={saveMySkills} />
                )}
            </div>

            <GapList gaps={gaps} />

            {jobArray.map((item) => {

                return (<JobCard key={item.jobId} companyName={item.companyName} jobRole={item.jobRole} jobStatus={item.jobStatus} jobId={item.jobId} jobDescription={item.jobDescription} resumeText={item.resumeText} skills={item.skills} fitScore={item.fitScore} missingSkills={item.missingSkills} extractionStatus={item.extractionStatus} onStatusChange={changeStatus} onSkillsSave={saveJobSkills} onRetry={retryExtraction}></JobCard>)

            })}
            <div className="rounded-lg border border-dashed border-gray-300 p-4">
                <form className="space-y-2" onSubmit={addJob}>
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
                        <h4 className="font-semibold text-gray-900 sm:mr-2">Add Job</h4>
                        <input className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm" type="text" value={companyName} placeholder='Company Name' onChange={(e) => setCompanyName(e.target.value)} />
                        <input className="flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm" type="text" value={jobRole} placeholder='Job Role' onChange={(e) => setJobRole(e.target.value)} />
                        <button className="rounded-md bg-indigo-600 px-3 py-1 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50" disabled={saving}>{saving ? "Saving… reading the description" : "Submit"}</button>
                    </div>
                    <textarea className="h-24 w-full rounded-md border border-gray-300 px-2 py-1 text-sm" value={jobDescription} placeholder='Paste the job description (optional)' onChange={(e) => setJobDescription(e.target.value)} />
                    <textarea className="h-24 w-full rounded-md border border-gray-300 px-2 py-1 text-sm" value={resumeText} placeholder='Paste the resume you sent (optional)' onChange={(e) => setResumeText(e.target.value)} />
                </form>



            </div>
        </div>

    )
}

// Log in, or sign up (which creates the account and then logs straight in).
const AuthForm = ({ onLogin }) => {
    const [mode, setMode] = useState("login")   // "login" or "signup"
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [error, setError] = useState("")

    const submit = async (e) => {
        e.preventDefault()
        setError("")

        if (mode === "signup") {
            const response = await fetch(`${API_URL}/auth/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            })
            if (response.status === 409) return setError("That email already has an account.")
            if (!response.ok) return setError("Use a real email and a password of at least 8 characters.")
        }

        // The login route takes a form (username + password), not JSON: that's the OAuth2 standard.
        const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            body: new URLSearchParams({ username: email, password }),
        })
        if (!response.ok) return setError("Wrong email or password.")

        onLogin((await response.json()).access_token)
    }

    return (
        <form className="space-y-3 rounded-lg border border-gray-200 bg-white p-6 shadow-sm" onSubmit={submit}>
            <h2 className="text-xl font-semibold text-gray-900">{mode === "login" ? "Log in" : "Create an account"}</h2>
            <input className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm" type="email" value={email} placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
            <input className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm" type="password" value={password} placeholder="Password" onChange={(e) => setPassword(e.target.value)} />
            {error && <p className="text-sm text-red-600">{error}</p>}
            <button className="w-full rounded-md bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700">{mode === "login" ? "Log in" : "Sign up"}</button>
            <button type="button" className="w-full text-sm text-indigo-600 hover:underline" onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError("") }}>
                {mode === "login" ? "No account? Sign up" : "Have an account? Log in"}
            </button>
        </form>
    )
}

const App = () => {
    // The token lives in localStorage so a refresh keeps you logged in; null = logged out.
    const [token, setToken] = useState(() => localStorage.getItem("token"))

    const login = (newToken) => {
        localStorage.setItem("token", newToken)
        setToken(newToken)
    }

    const logout = () => {
        localStorage.removeItem("token")
        setToken(null)
    }

    return (
        <div className="mx-auto min-h-screen max-w-2xl bg-gray-50 p-6">
            <div className="mb-6 flex items-center justify-between">
                <h1 className="text-3xl font-bold text-gray-900">Job Tracker</h1>
                {token && <button className="text-sm text-gray-600 hover:underline" onClick={logout}>Log out</button>}
            </div>
            {token ? <JobList token={token} onLogout={logout} /> : <AuthForm onLogin={login} />}
        </div>
    )
}

export default App
