import { Link } from 'react-router'
import { Header } from '../components/Header'

// Who to contact about your data. Shown on the page, so use an address you're happy to publish.
const CONTACT_EMAIL = "ashwinsuresh.x@gmail.com"

const Section = ({ title, children }) => (
    <section className="mt-8">
        <h2 className="text-lg font-extrabold text-text">{title}</h2>
        <div className="mt-2 space-y-2 text-muted">{children}</div>
    </section>
)

// Plain-language privacy policy for the Huntboard website and browser extension.
export const PrivacyPage = () => {
    return (
        <div className="min-h-screen bg-background">
            <Header />
            <main className="page-width max-w-3xl py-10">
                <Link to="/" className="inline-flex min-h-11 items-center text-sm font-bold text-primary hover:underline">← Huntboard</Link>
                <h1 className="mt-2 text-3xl font-extrabold text-text">Privacy</h1>
                <p className="mt-2 text-muted-2">Last updated 18 October 2026</p>

                <Section title="What Huntboard stores">
                    <p>Your account: your email address and a securely hashed password (never the password itself).</p>
                    <p>What you add: the jobs you save (company, role, location, the job's web address, the description, its status), the resume text you choose to paste, and the skills you list.</p>
                    <p>Short-lived sign-in codes, stored only as a hash and expiring after 15 minutes.</p>
                </Section>

                <Section title="The browser extension">
                    <p>The extension reads the page you are on <strong>only when you click its icon</strong>, and only that tab. It never reads pages in the background or records your browsing.</p>
                    <p>When you click it, it sends that page's address, its text (or the text you selected) and its structured job data to Huntboard's own server, so the job's details can be filled in for you to check. Nothing is saved until you press Save.</p>
                    <p>Your sign-in is kept in the extension's own storage on your computer, and is sent only to Huntboard's server.</p>
                </Section>

                <Section title="Services that process your data">
                    <p><strong>OpenAI</strong> reads job descriptions and page text to pick out skills and job details.</p>
                    <p><strong>Resend</strong> sends your verification and password-reset emails.</p>
                    <p><strong>Render</strong> and <strong>Neon</strong> host the website, server and database.</p>
                    <p>Each receives only what it needs for that job.</p>
                </Section>

                <Section title="What Huntboard never does">
                    <p>No ads, no tracking or analytics, and your data is never sold or shared for marketing.</p>
                </Section>

                <Section title="Deleting your data">
                    <p>Email <a className="font-bold text-primary hover:underline" href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a> from your account's address and your account and everything in it will be deleted. To remove the extension, remove it from your browser's add-ons page.</p>
                </Section>
            </main>
        </div>
    )
}
