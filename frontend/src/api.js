// The API's address comes from an environment variable (see .env.development).
export const API_URL = import.meta.env.VITE_API_URL

// Every API call goes through here: it adds the token, and a 401 (expired or bad token) logs out.
export const makeApi = (token, onLogout) => async (path, options = {}) => {
    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers: { ...options.headers, Authorization: `Bearer ${token}` },
    })
    if (response.status === 401) onLogout()
    return response
}
