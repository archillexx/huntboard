// Big number + thin 8px bar. Display only: the score itself comes from the API (your fit_score).
export const FitScore = ({ score }) => {
    if (score === null) {
        return <p className="text-sm text-muted-2">No skills listed yet</p>
    }

    const rounded = Math.round(score)
    const good = rounded >= 75   // green from 75%, amber below
    return (
        <div>
            <div className="flex items-baseline gap-1.5">
                <span className={`text-3xl font-extrabold ${good ? "text-fit-good" : "text-fit-low"}`}>{rounded}%</span>
                <span className="text-sm font-bold text-muted-2">fit</span>
            </div>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-track" role="progressbar" aria-valuenow={rounded} aria-valuemin={0} aria-valuemax={100} aria-label="Fit score">
                <div className={`h-full rounded-full ${good ? "bg-fit-good-bar" : "bg-fit-low-bar"}`} style={{ width: `${rounded}%` }} />
            </div>
        </div>
    )
}
