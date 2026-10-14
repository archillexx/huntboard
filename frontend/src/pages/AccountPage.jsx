import { useState } from 'react'
import { Link } from 'react-router'
import { makeApi } from '../api'
import { Header } from '../components/Header'
import { PasswordInput } from '../components/PasswordInput'

const inputClass = "w-full rounded-[14px] border border-outline bg-surface px-3.5 py-3 text-text focus:border-primary focus:outline-2 focus:outline-primary"

// Account settings: for now, changing your password.
export const AccountPage = ({ token, onLogout, onNewToken }) => {
    const api = makeApi(token, onLogout)
    const email = localStorage.getItem("email") ?? ""

    const [current, setCurrent] = useState("")
    const [next, setNext] = useState("")
    const [error, setError] = useState("")
    const [done, setDone] = useState(false)
    const [saving, setSaving] = useState(false)

    const changePassword = async (e) => {
        e.preventDefault()
        setError("")
        setDone(false)
        if (next.length < 8) return setError("The new password needs at least 8 characters.")
        setSaving(true)
        try {
            const response = await api("/auth/change-password", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ current_password: current, new_password: next }),
            })
            const body = await response.json().catch(() => ({}))
            if (!response.ok) return setError(typeof body.detail === "string" ? body.detail : "Couldn't change your password.")
            // The old token stops working after a change, so swap in the fresh one straight away.
            onNewToken(body.access_token)
            setCurrent("")
            setNext("")
            setDone(true)
        } catch {
            setError("Can't reach the server. Is the backend running?")
        } finally {
            setSaving(false)
        }
    }

    return (
        <div className="min-h-screen bg-background">
            <Header>
                <button className="min-h-11 rounded-full border border-outline px-4 text-sm font-bold text-text hover:bg-surface-variant focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary" onClick={onLogout}>
                    Log out
                </button>
            </Header>
            <main className="page-width py-8">
                <Link to="/jobs" className="inline-flex min-h-11 items-center text-sm font-bold text-primary hover:underline">← Back to applications</Link>
                <h1 className="mt-2 text-3xl font-extrabold text-text">Account</h1>
                {email && <p className="mt-1 text-muted">Signed in as <span className="font-bold text-text">{email}</span></p>}

                <form className="mt-8 max-w-md rounded-[20px] border border-border bg-surface p-6 shadow-sm dark:shadow-none" onSubmit={changePassword} noValidate>
                    <h2 className="text-lg font-extrabold text-text">Change password</h2>
                    <p className="mt-1 text-sm text-muted-2">This signs you out everywhere else.</p>

                    <div className="mt-5">
                        <label htmlFor="current-password" className="text-sm font-bold text-text">Current password</label>
                        <PasswordInput id="current-password" className={inputClass} autoComplete="current-password" value={current} onChange={(e) => setCurrent(e.target.value)} />
                    </div>
                    <div className="mt-4">
                        <label htmlFor="new-password" className="text-sm font-bold text-text">New password</label>
                        <PasswordInput id="new-password" className={inputClass} autoComplete="new-password" value={next} onChange={(e) => setNext(e.target.value)} aria-describedby="new-password-hint" />
                        <p id="new-password-hint" className="mt-1.5 text-sm text-muted-2">At least 8 characters.</p>
                    </div>

                    {error && <p className="mt-4 rounded-xl bg-missing px-3.5 py-2.5 text-sm font-bold text-on-missing" role="alert">{error}</p>}
                    {done && <p className="mt-4 rounded-xl bg-replied px-3.5 py-2.5 text-sm font-bold text-on-replied" role="status">Password changed. Other devices are signed out.</p>}

                    <button className="mt-6 min-h-11 rounded-full bg-primary px-5 text-sm font-bold text-on-primary hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60" disabled={saving}>
                        {saving ? "Saving…" : "Change password"}
                    </button>
                </form>
            </main>
        </div>
    )
}
