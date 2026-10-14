// One colour pair per status (tokens in index.css). Written out in full so Tailwind can find the class names.
const STATUS_CLASSES = {
    Interview: "bg-interview text-on-interview",
    Applied: "bg-applied text-on-applied",
    Considering: "bg-considering text-on-considering",
    Replied: "bg-replied text-on-replied",
    Rejected: "bg-rejected text-on-rejected",
    Ghosted: "bg-ghosted text-on-ghosted",
}

export const StatusChip = ({ status }) => {
    return (
        <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold ${STATUS_CLASSES[status] ?? "bg-surface-variant text-muted"}`}>
            {status}
        </span>
    )
}
