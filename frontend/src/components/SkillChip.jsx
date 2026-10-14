// A skill the job asks for: neutral, or red with "· missing" when it isn't in my skills.
export const SkillChip = ({ name, missing = false }) => {
    return (
        <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold ${missing ? "bg-missing text-on-missing" : "bg-surface-variant text-muted"}`}>
            {name}{missing && " · missing"}
        </span>
    )
}
