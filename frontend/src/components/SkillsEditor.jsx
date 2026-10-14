import { useState } from 'react'

// A comma-separated text box for a list of skills, saved with one button.
export const SkillsEditor = ({ id, label, initialSkills, placeholder, onSave }) => {
    const [text, setText] = useState(initialSkills.join(", "))

    const save = (e) => {
        e.preventDefault()
        onSave(text.split(","))
    }

    return (
        <form onSubmit={save}>
            <label htmlFor={id} className="text-sm font-bold text-text">{label}</label>
            <div className="mt-1.5 flex gap-2">
                <input id={id} className="min-h-11 min-w-0 flex-1 rounded-xl border border-outline bg-surface px-3 text-sm text-text placeholder:text-muted-2 focus:outline-2 focus:outline-primary"
                    type="text" value={text} placeholder={placeholder} onChange={(e) => setText(e.target.value)} />
                <button className="min-h-11 rounded-full bg-primary-container px-4 text-sm font-bold text-on-primary-container hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">Save</button>
            </div>
        </form>
    )
}
