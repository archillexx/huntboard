import { useEffect, useState } from 'react'

// "light" or "dark" if you've used the toggle; nothing saved = follow the system setting.
const savedTheme = () => localStorage.getItem("theme")
const systemTheme = () => window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"

export const useTheme = () => {
    const [theme, setTheme] = useState(() => savedTheme() ?? systemTheme())

    // Keep <html class="dark"> in step with the theme; every dark: style keys off that class.
    useEffect(() => {
        document.documentElement.classList.toggle("dark", theme === "dark")
    }, [theme])

    // Until you pick one yourself, follow the system if it changes while the page is open.
    useEffect(() => {
        const media = window.matchMedia("(prefers-color-scheme: dark)")
        const follow = () => { if (!savedTheme()) setTheme(systemTheme()) }
        media.addEventListener("change", follow)
        return () => media.removeEventListener("change", follow)
    }, [])

    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark"
        localStorage.setItem("theme", next)
        setTheme(next)
    }

    return { theme, toggleTheme }
}
