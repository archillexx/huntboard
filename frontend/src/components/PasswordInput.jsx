import { useState } from 'react'

// A password field with an eye button that shows/hides what you typed.
// Showing it just switches the input's type between "password" and "text"; nothing is sent anywhere.
// Other props (id, value, onChange, autoComplete, aria-*) pass straight through to the <input>.
export const PasswordInput = ({ className, ...inputProps }) => {
    const [visible, setVisible] = useState(false)

    return (
        <div className="relative mt-1.5">
            <input {...inputProps} type={visible ? "text" : "password"} className={`${className} pr-12`} />
            <button type="button" onClick={() => setVisible(!visible)}
                aria-label={visible ? "Hide password" : "Show password"} aria-pressed={visible}
                className="absolute inset-y-0 right-0 flex w-12 items-center justify-center rounded-r-[14px] text-muted hover:text-text focus-visible:outline-2 focus-visible:outline-primary">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                    <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" />
                    <circle cx="12" cy="12" r="3" />
                    {/* a slash through the eye while the password is showing = "click to hide" */}
                    {visible && <path d="M3 3l18 18" />}
                </svg>
            </button>
        </div>
    )
}
