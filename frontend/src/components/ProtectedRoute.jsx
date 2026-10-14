import { Navigate } from 'react-router'

// Logged out? Send them to /login instead of showing the page.
// This only hides pages: the real lock is the backend refusing requests without a valid token.
export const ProtectedRoute = ({ token, children }) => {
    if (!token) return <Navigate to="/login" replace />
    return children
}
