// The Huntboard tile + wordmark. Colours come from the logo tokens, so dark mode swaps them.
export const Logo = () => {
    return (
        <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-logo-tile">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="12" cy="12" r="7.5" className="stroke-logo-ink" strokeWidth="2" />
                    <circle cx="12" cy="12" r="3.6" className="stroke-logo-ink" strokeWidth="2" />
                    <circle cx="12" cy="12" r="1.5" className="fill-logo-dot" />
                    <path d="M12 1.8v3.4M12 18.8v3.4M1.8 12h3.4M18.8 12h3.4" className="stroke-logo-ink" strokeWidth="2" strokeLinecap="round" />
                </svg>
            </div>
            <span className="text-xl font-extrabold tracking-[-0.01em] text-text">
                Hunt<span className="text-primary">board</span>
            </span>
        </div>
    )
}
