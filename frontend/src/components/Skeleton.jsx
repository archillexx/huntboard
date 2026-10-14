// Grey placeholder shapes shown while data loads. motion-reduce: no pulsing for people who turn animations off.
const Block = ({ className }) => <div className={`animate-pulse rounded-full bg-surface-variant motion-reduce:animate-none ${className}`} />

export const SkeletonCard = () => {
    return (
        <div className="rounded-[20px] border border-border bg-surface p-5" aria-hidden="true">
            <Block className="h-5 w-2/3" />
            <Block className="mt-2 h-4 w-1/3" />
            <Block className="mt-6 h-8 w-20" />
            <Block className="mt-3 h-2 w-full" />
            <Block className="mt-5 h-10 w-full" />
        </div>
    )
}

export const SkeletonLines = ({ count = 4 }) => {
    return (
        <div className="space-y-3" aria-hidden="true">
            {Array.from({ length: count }, (_, i) => <Block key={i} className="h-4 w-full" />)}
        </div>
    )
}
