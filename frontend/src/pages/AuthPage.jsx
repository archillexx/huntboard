import { useState } from 'react'
import { Link } from 'react-router'
import { API_URL } from '../api'
import { Header } from '../components/Header'
import { PasswordInput } from '../components/PasswordInput'

const inputClass = "mt-1.5 w-full rounded-[14px] border border-outline bg-surface px-3.5 py-3 text-text placeholder:text-muted-2 focus:border-primary focus:outline-2 focus:outline-primary"

// Turn an error response into messages keyed by where they show: "email", "password" or "form".
// 422 = FastAPI validation: detail is a list, each with loc like ["body", "password"] and a msg.
const errorsFrom = async (response) => {
    const body = await response.json().catch(() => ({}))
    if (Array.isArray(body.detail)) {
        const errors = {}
        for (const item of body.detail) {
            const field = item.loc?.at(-1)
            errors[field === "email" || field === "password" ? field : "form"] = item.msg
        }
        return errors
    }
    // 409 is about the email; anything else (e.g. 401) is about the form as a whole.
    return response.status === 409 ? { email: body.detail } : { form: body.detail ?? "Something went wrong. Try again." }
}

// Log in, or sign up (which creates the account and then logs straight in).
export const AuthPage = ({ mode, onLogin }) => {   // mode: "login" or "signup", from the route
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [errors, setErrors] = useState({})
    const [submitting, setSubmitting] = useState(false)

    const signup = mode === "signup"

    const submit = async (e) => {
        e.preventDefault()
        setErrors({})
        setSubmitting(true)
        try {
            if (signup) {
                const response = await fetch(`${API_URL}/auth/signup`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                })
                if (!response.ok) return setErrors(await errorsFrom(response))
            }

            // The login route takes a form (username + password), not JSON: that's the OAuth2 standard.
            const response = await fetch(`${API_URL}/auth/login`, {
                method: "POST",
                body: new URLSearchParams({ username: email, password }),
            })
            if (!response.ok) return setErrors(await errorsFrom(response))

            onLogin((await response.json()).access_token, email)
        } catch {
            // fetch itself throws when the server can't be reached at all.
            setErrors({ form: "Can't reach the server. Is the backend running?" })
        } finally {
            setSubmitting(false)
        }
    }

    return (
        <div className="min-h-screen bg-background">
            <Header />
            <main className="page-width flex justify-center py-12 sm:py-20">
                <form className="w-full max-w-md rounded-[28px] border border-border bg-surface p-6 shadow-lg shadow-primary/10 sm:p-8 dark:shadow-none" onSubmit={submit} noValidate>
                    <h1 className="text-2xl font-extrabold text-text">{signup ? "Create your account" : "Welcome back"}</h1>
                    <p className="mt-1 text-sm text-muted-2">{signup ? "Start tracking your applications." : "Sign in to see your applications."}</p>

                    <div className="mt-6">
                        <label htmlFor="email" className="text-sm font-bold text-text">Email</label>
                        <input id="email" className={inputClass} type="email" autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)}
                            aria-invalid={!!errors.email} aria-describedby={errors.email ? "email-error" : undefined} />
                        {errors.email && <p id="email-error" className="mt-1.5 text-sm text-on-missing">{errors.email}</p>}
                    </div>

                    <div className="mt-4">
                        <label htmlFor="password" className="text-sm font-bold text-text">Password</label>
                        {/* PasswordInput adds its own top margin, so mt-1.5 comes off the input's classes. */}
                        <PasswordInput id="password" className={inputClass.replace("mt-1.5 ", "")} autoComplete={signup ? "new-password" : "current-password"} value={password} onChange={(e) => setPassword(e.target.value)}
                            aria-invalid={!!errors.password} aria-describedby={errors.password ? "password-error" : signup ? "password-hint" : undefined} />
                        {errors.password
                            ? <p id="password-error" className="mt-1.5 text-sm text-on-missing">{errors.password}</p>
                            : signup && <p id="password-hint" className="mt-1.5 text-sm text-muted-2">At least 8 characters.</p>}
                    </div>

                    {errors.form && <p className="mt-4 rounded-xl bg-missing px-3.5 py-2.5 text-sm font-bold text-on-missing" role="alert">{errors.form}</p>}

                    <button className="mt-6 flex min-h-12 w-full items-center justify-center rounded-full bg-primary px-5 font-bold text-on-primary hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary disabled:opacity-60" disabled={submitting}>
                        {submitting ? (signup ? "Creating account…" : "Signing in…") : (signup ? "Create account" : "Sign in")}
                    </button>

                    <p className="mt-5 text-center text-sm text-muted">
                        {signup ? "Have an account? " : "No account? "}
                        <Link className="inline-flex min-h-11 items-center font-bold text-primary hover:underline" to={signup ? "/login" : "/signup"}>
                            {signup ? "Sign in" : "Create one"}
                        </Link>
                    </p>
                </form>
            </main>
        </div>
    )
}
