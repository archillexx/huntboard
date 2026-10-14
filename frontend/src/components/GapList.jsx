import { useState } from 'react'
import { SkeletonLines } from './Skeleton'

const TOP = 5   // how many gaps show before "Show all"

// My most-missed skills across all jobs, most-missed first. gaps === null means still loading.
export const GapList = ({ gaps, error, onRetry }) => {
    const [showAll, setShowAll] = useState(false)
    // The list arrives ranked (most-missed first), so the top 5 are just the first 5.
    const shown = gaps && !showAll ? gaps.slice(0, TOP) : gaps

    return (
        <section className="rounded-[20px] border border-border bg-surface p-5 shadow-sm dark:shadow-none" aria-labelledby="gaps-title">
            <h2 id="gaps-title" className="font-extrabold text-text">Most missed skills</h2>
            <div className="mt-4">
                {error ? (
                    <div className="text-sm text-muted">
                        <p>Couldn't load your skill gaps.</p>
                        <button className="mt-2 min-h-11 font-bold text-primary hover:underline" onClick={onRetry}>Try again</button>
                    </div>
                ) : gaps === null ? (
                    <SkeletonLines />
                ) : gaps.length === 0 ? (
                    <p className="text-sm text-muted-2">No gaps yet. Add skills to your jobs to see them here.</p>
                ) : (
                    <>
                    <ol className="space-y-2.5 text-sm">
                        {shown.map((gap) => (
                            <li key={gap.skill} className="flex items-center justify-between gap-3">
                                <span className="font-bold text-text">{gap.skill}</span>
                                <span className="rounded-full bg-missing px-2.5 py-0.5 text-xs font-bold text-on-missing">
                                    {gap.count} {gap.count === 1 ? "job" : "jobs"}
                                </span>
                            </li>
                        ))}
                    </ol>
                    {gaps.length > TOP && (
                        <button className="mt-3 min-h-11 text-sm font-bold text-primary hover:underline focus-visible:outline-2 focus-visible:outline-primary" onClick={() => setShowAll(!showAll)} aria-expanded={showAll}>
                            {showAll ? "Show top 5" : `Show all (${gaps.length})`}
                        </button>
                    )}
                    </>
                )}
            </div>
        </section>
    )
}
