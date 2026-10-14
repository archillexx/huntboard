import { useEffect, useState } from 'react'
import { Link } from 'react-router'
import { API_URL } from '../api'
import { Header } from '../components/Header'
import { PasswordInput } from '../components/PasswordInput'

const COOLDOWN = 60   // seconds; matches RESEND_COOLDOWN in backend/codes.py
const inputClass = "w-full rounded-[14px] border border-outline bg-surface px-3.5 py-3 text-text placeholder:text-muted-2 focus:border-primary focus:outline-2 focus:outline-primary"
const buttonClass = "mt-6 flex min-h-12 w-full items-center justify-center rounded-full bg-primary px-5 font-bold text-on-primary hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60"

// Two steps on one page: 1) ask for a code by email, 2) enter the code + a new password.
export const ForgotPasswordPage = ({ onLogin }) => {
    const [step, setStep] = useState("email")   // "email" or "reset"
    const [email, setEmail] = useState("")
    const [code, setCode] = useState("")
    const [password, setPassword] = useState("")
    const [error, setError] = useState("")
    const [notice, setNotice] = useState("")
    const [busy, setBusy] = useState(false)
    const [secondsLeft, setSecondsLeft] = useState(0)

    // Resend countdown, same pattern as the verify page.
    useEffect(() => {
        if (secondsLeft <= 0) return
        const timer = setTimeout(() => setSecondsLeft(secondsLeft - 1), 1000)
        return () => clearTimeout(timer)
    }, [secondsLeft])

    const post = (path, body) => fetch(`${API_URL}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    })

    // The reply is the same whether or not the account exists, so the page always moves on.
    const sendCode = async (e) => {
        e?.preventDefault()
        setError("")
        setNotice("")
        if (!email.trim()) return setError("Enter your email.")
        setBusy(true)
        try {
            const response = await post("/auth/forgot-password", { email })
            if (response.status === 422) return setError("Enter a real email address.")
            if (!response.ok) return setError("We couldn't send the code. Try again in a minute.")
            setSecondsLeft(COOLDOWN)
            if (step === "reset") setNotice("If that email has an account, a new code is on its way.")
            setStep("reset")
        } catch {
            setError("Can't reach the server. Is the backend running?")
        } finally {
            setBusy(false)
        }
    }

    const resetPassword = async (e) => {
        e.preventDefault()
        setError("")
        setNotice("")
        if (password.length < 8) return setError("The new password needs at least 8 characters.")
        setBusy(true)
        try {
            const response = await post("/auth/reset-password", { email, code, new_password: password })
            const body = await response.json().catch(() => ({}))
            if (!response.ok) return setError(typeof body.detail === "string" ? body.detail : "Enter the 6-digit code from the email.")
            onLogin(body.access_token, email)
        } catch {
            setError("Can't reach the server. Is the backend running?")
        } finally {
            setBusy(false)
        }
    }

    const messages = (
        <>
            {error && <p className="mt-4 rounded-xl bg-missing px-3.5 py-2.5 text-sm font-bold text-on-missing" role="alert">{error}</p>}
            {notice && <p className="mt-4 text-sm text-muted" role="status">{notice}</p>}
        </>
    )

    return (
        <div className="min-h-screen bg-background">
            <Header />
            <main className="page-width flex justify-center py-12 sm:py-20">
                <div className="w-full max-w-md rounded-[28px] border border-border bg-surface p-6 shadow-lg shadow-primary/10 sm:p-8 dark:shadow-none">
                    {step === "email" ? (
                        <form onSubmit={sendCode} noValidate>
                            <h1 className="text-2xl font-extrabold text-text">Reset your password</h1>
                            <p className="mt-1 text-sm text-muted-2">Enter your email and we'll send you a 6-digit code.</p>
                            <div className="mt-6">
                                <label htmlFor="reset-email" className="text-sm font-bold text-text">Email</label>
                                <input id="reset-email" autoFocus type="email" autoComplete="email" className={`mt-1.5 ${inputClass}`} value={email} onChange={(e) => setEmail(e.target.value)} />
                            </div>
                            {messages}
                            <button className={buttonClass} disabled={busy}>{busy ? "Sending…" : "Send code"}</button>
                        </form>
                    ) : (
                        <form onSubmit={resetPassword} noValidate>
                            <h1 className="text-2xl font-extrabold text-text">Check your email</h1>
                            <p className="mt-1 text-sm text-muted-2">
                                If <span className="font-bold text-text">{email}</span> has an account, we sent it a code. It expires in 15 minutes.
                            </p>
                            <div className="mt-6">
                                <label htmlFor="reset-code" className="text-sm font-bold text-text">Code</label>
                                <input id="reset-code" autoFocus inputMode="numeric" autoComplete="one-time-code" maxLength={6}
                                    className={`mt-1.5 ${inputClass} text-center text-2xl font-extrabold tracking-[0.5em]`}
                                    value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))} />
                            </div>
                            <div className="mt-4">
                                <label htmlFor="reset-password" className="text-sm font-bold text-text">New password</label>
                                <PasswordInput id="reset-password" className={inputClass} autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} aria-describedby="reset-password-hint" />
                                <p id="reset-password-hint" className="mt-1.5 text-sm text-muted-2">At least 8 characters. This signs you out everywhere else.</p>
                            </div>
                            {messages}
                            <button className={buttonClass} disabled={busy || code.length !== 6}>{busy ? "Saving…" : "Set new password"}</button>
                            <button type="button" onClick={() => sendCode()} disabled={secondsLeft > 0 || busy}
                                className="mt-4 min-h-11 text-sm font-bold text-primary hover:underline disabled:text-muted-2 disabled:no-underline">
                                {secondsLeft > 0 ? `Resend code in ${secondsLeft}s` : "Resend code"}
                            </button>
                        </form>
                    )}
                    <p className="mt-4 text-center text-sm text-muted">
                        Remembered it? <Link className="inline-flex min-h-11 items-center font-bold text-primary hover:underline" to="/login">Sign in</Link>
                    </p>
                </div>
            </main>
        </div>
    )
}
