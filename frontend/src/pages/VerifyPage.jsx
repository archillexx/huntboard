import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router'
import { API_URL } from '../api'
import { Header } from '../components/Header'

const COOLDOWN = 60   // seconds; matches RESEND_COOLDOWN in backend/codes.py

// Type the 6-digit code from your email. Success logs you straight in.
export const VerifyPage = ({ onLogin }) => {
    // The email rides in the URL (/verify?email=...). It's only a hint for the form:
    // the backend still demands the right code, so editing the URL gets nobody anywhere.
    const [searchParams] = useSearchParams()
    const email = searchParams.get("email") ?? ""

    const [code, setCode] = useState("")
    const [error, setError] = useState("")
    const [notice, setNotice] = useState("")
    const [submitting, setSubmitting] = useState(false)
    const [secondsLeft, setSecondsLeft] = useState(COOLDOWN)   // a code was just sent, so start waiting

    // Count down once a second until Resend is allowed. The cleanup stops the old timer
    // before the next tick, so there's only ever one running.
    useEffect(() => {
        if (secondsLeft <= 0) return
        const timer = setTimeout(() => setSecondsLeft(secondsLeft - 1), 1000)
        return () => clearTimeout(timer)
    }, [secondsLeft])

    const verify = async (e) => {
        e.preventDefault()
        setError("")
        setNotice("")
        setSubmitting(true)
        try {
            const response = await fetch(`${API_URL}/auth/verify`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, code }),
            })
            const body = await response.json().catch(() => ({}))
            if (!response.ok) {
                // 422 = not 6 characters (Pydantic); 400 = the backend's own message (wrong, expired, too many tries).
                return setError(Array.isArray(body.detail) ? "Enter the 6-digit code from the email." : body.detail)
            }
            onLogin(body.access_token, email)
        } catch {
            setError("Can't reach the server. Is the backend running?")
        } finally {
            setSubmitting(false)
        }
    }

    const resend = async () => {
        setError("")
        setNotice("")
        setSecondsLeft(COOLDOWN)
        try {
            const response = await fetch(`${API_URL}/auth/resend-code`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email }),
            })
            if (!response.ok) return setError("We couldn't send a new code. Try again in a minute.")
            setNotice("A new code is on its way. Check your spam folder too.")
        } catch {
            setError("Can't reach the server. Is the backend running?")
        }
    }

    if (!email) {
        return (
            <div className="min-h-screen bg-background">
                <Header />
                <main className="page-width py-20 text-center text-muted">
                    <p>Nothing to verify here.</p>
                    <Link className="mt-3 inline-flex min-h-11 items-center font-bold text-primary hover:underline" to="/signup">Create an account</Link>
                </main>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-background">
            <Header />
            <main className="page-width flex justify-center py-12 sm:py-20">
                <form className="w-full max-w-md rounded-[28px] border border-border bg-surface p-6 shadow-lg shadow-primary/10 sm:p-8 dark:shadow-none" onSubmit={verify} noValidate>
                    <h1 className="text-2xl font-extrabold text-text">Check your email</h1>
                    <p className="mt-1 text-sm text-muted-2">
                        We sent a 6-digit code to <span className="font-bold text-text">{email}</span>. It expires in 15 minutes.
                    </p>

                    <div className="mt-6">
                        <label htmlFor="code" className="text-sm font-bold text-text">Verification code</label>
                        {/* one-time-code lets phones offer the code straight from the email or SMS */}
                        <input id="code" autoFocus inputMode="numeric" autoComplete="one-time-code" maxLength={6}
                            value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                            aria-invalid={!!error} aria-describedby={error ? "code-error" : undefined}
                            className="mt-1.5 w-full rounded-[14px] border border-outline bg-surface px-3.5 py-3 text-center text-2xl font-extrabold tracking-[0.5em] text-text focus:border-primary focus:outline-2 focus:outline-primary" />
                        {error && <p id="code-error" className="mt-1.5 text-sm text-on-missing" role="alert">{error}</p>}
                        {notice && <p className="mt-1.5 text-sm text-muted" role="status">{notice}</p>}
                    </div>

                    <button className="mt-6 flex min-h-12 w-full items-center justify-center rounded-full bg-primary px-5 font-bold text-on-primary hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60"
                        disabled={submitting || code.length !== 6}>
                        {submitting ? "Checking…" : "Verify and continue"}
                    </button>

                    <div className="mt-5 flex items-center justify-between text-sm">
                        <button type="button" onClick={resend} disabled={secondsLeft > 0}
                            className="min-h-11 font-bold text-primary hover:underline disabled:text-muted-2 disabled:no-underline">
                            {secondsLeft > 0 ? `Resend code in ${secondsLeft}s` : "Resend code"}
                        </button>
                        <Link className="inline-flex min-h-11 items-center text-muted hover:underline" to="/signup">Wrong email?</Link>
                    </div>
                </form>
            </main>
        </div>
    )
}
