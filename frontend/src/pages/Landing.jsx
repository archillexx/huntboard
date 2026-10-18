import { Link } from 'react-router'
import { FitScore } from '../components/FitScore'
import { Header } from '../components/Header'
import { SkillChip } from '../components/SkillChip'
import { StatusChip } from '../components/StatusChip'

// Shared button looks: pill shape, 44px tall, visible focus ring.
const filledButton = "inline-flex min-h-11 items-center justify-center rounded-full bg-primary px-5 text-sm font-bold text-on-primary hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
const textButton = "inline-flex min-h-11 items-center justify-center rounded-full px-4 text-sm font-bold text-primary hover:bg-surface-variant focus-visible:outline-2 focus-visible:outline-primary"
const outlineButton = "inline-flex min-h-11 items-center justify-center rounded-full border border-outline px-5 text-sm font-bold text-primary hover:bg-surface-variant focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"

const FEATURES = [
    {
        title: "Track every application",
        text: "Company, role, status and the exact resume you sent, all in one place.",
        icon: <path d="M4 6h16M4 12h16M4 18h10" />,
    },
    {
        title: "AI skill extraction and fit score",
        text: "Paste the job description and the skills are pulled out for you, with a fit score against your own skills.",
        icon: <path d="M12 3l2.2 5.8L20 11l-5.8 2.2L12 19l-2.2-5.8L4 11l5.8-2.2z" />,
    },
    {
        title: "Know your skill gaps",
        text: "See which skills you're missing most across every job, so you know what to learn next.",
        icon: <><circle cx="12" cy="12" r="8" /><circle cx="12" cy="12" r="3" /></>,
    },
]

// Decorative only: a hardcoded example of what a job card looks like.
const PreviewCard = () => {
    return (
        <div className="rounded-[20px] border border-border bg-surface p-6 shadow-lg 2xl:p-8 shadow-primary/10 dark:shadow-none" aria-hidden="true">
            <div className="flex items-start justify-between gap-3">
                <div>
                    <p className="text-lg font-extrabold text-text">Frontend Engineer</p>
                    <p className="text-sm text-muted-2">Example Co.</p>
                </div>
                <StatusChip status="Interview" />
            </div>
            <div className="mt-5">
                <FitScore score={80} />
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
                <SkillChip name="react" />
                <SkillChip name="typescript" />
                <SkillChip name="css" />
                <SkillChip name="graphql" missing />
            </div>
        </div>
    )
}

export const Landing = () => {
    return (
        <div className="min-h-screen bg-background">
            <Header>
                <Link to="/login" className={textButton}>Sign in</Link>
                <Link to="/signup" className={`${filledButton} max-sm:hidden`}>Create account</Link>
            </Header>

            <main className="page-width py-12 sm:py-20 2xl:py-28">
                <section className="grid items-center gap-12 md:grid-cols-2 2xl:gap-20">
                    <div>
                        <span className="inline-flex rounded-full bg-primary-container px-3 py-1 text-xs font-bold text-on-primary-container">
                            AI skill extraction built in
                        </span>
                        <h1 className="mt-5 text-4xl font-extrabold leading-tight tracking-tight text-text sm:text-5xl 2xl:text-6xl">
                            Track every application. See your fit. Know your gaps.
                        </h1>
                        <p className="mt-5 text-lg text-muted 2xl:text-xl">
                            Save each job with the resume you sent. Huntboard reads the description, scores how well you fit, and shows the skills you're missing.
                        </p>
                        <div className="mt-8 flex flex-wrap gap-3">
                            <Link to="/signup" className={filledButton}>Get started</Link>
                            <Link to="/login" className={outlineButton}>Sign in</Link>
                        </div>
                    </div>
                    <PreviewCard />
                </section>

                <section className="mt-20 grid gap-4 sm:grid-cols-3">
                    {FEATURES.map((feature) => (
                        <div key={feature.title} className="rounded-[20px] border border-border bg-surface p-6 shadow-sm dark:shadow-none">
                            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary-container text-on-primary-container">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                                    {feature.icon}
                                </svg>
                            </div>
                            <h2 className="mt-4 font-extrabold text-text">{feature.title}</h2>
                            <p className="mt-2 text-sm text-muted">{feature.text}</p>
                        </div>
                    ))}
                </section>
            </main>
            <footer className="page-width pb-10 text-sm text-muted-2">
                <Link to="/privacy" className="inline-flex min-h-11 items-center hover:underline">Privacy</Link>
            </footer>
        </div>
    )
}
