import { useState } from 'react'
import { Navigate, Route, Routes, useNavigate } from 'react-router'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthPage } from './pages/AuthPage'
import { Dashboard } from './pages/Dashboard'
import { Landing } from './pages/Landing'
import { VerifyPage } from './pages/VerifyPage'

const App = () => {
    const navigate = useNavigate()

    // The token lives in localStorage so a refresh keeps you logged in; null = logged out.
    const [token, setToken] = useState(() => localStorage.getItem("token"))

    // The email is kept only to show your initial in the header; the token is what proves who you are.
    const login = (newToken, email) => {
        localStorage.setItem("token", newToken)
        localStorage.setItem("email", email.trim().toLowerCase())
        setToken(newToken)
        navigate("/jobs")
    }

    // No navigate here: once the token is null, ProtectedRoute sends you to /login.
    const logout = () => {
        localStorage.removeItem("token")
        localStorage.removeItem("email")
        setToken(null)
    }

    // Already logged in? The landing, login and signup pages skip ahead to your jobs.
    const authPage = (mode) => token ? <Navigate to="/jobs" replace /> : <AuthPage key={mode} mode={mode} onLogin={login} />

    return (
        <Routes>
            <Route path="/" element={token ? <Navigate to="/jobs" replace /> : <Landing />} />
            <Route path="/login" element={authPage("login")} />
            <Route path="/signup" element={authPage("signup")} />
            <Route path="/verify" element={token ? <Navigate to="/jobs" replace /> : <VerifyPage onLogin={login} />} />
            <Route path="/jobs" element={
                <ProtectedRoute token={token}>
                    <Dashboard token={token} onLogout={logout} />
                </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

export default App
