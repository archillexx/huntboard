import { Link } from 'react-router'
import { useTheme } from '../theme'
import { Logo } from './Logo'
import { ThemeToggle } from './ThemeToggle'

// The top bar every page shares: logo on the left, theme toggle + the page's own buttons (children) on the right.
export const Header = ({ children }) => {
    const { theme, toggleTheme } = useTheme()
    return (
        <header className="border-b border-border bg-header">
            <div className="page-width flex items-center justify-between gap-2 py-3">
                <Link to="/" aria-label="Huntboard home" className="rounded-xl focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
                    <Logo />
                </Link>
                <div className="flex items-center gap-1 sm:gap-2">
                    <ThemeToggle theme={theme} onToggle={toggleTheme} />
                    {children}
                </div>
            </div>
        </header>
    )
}
