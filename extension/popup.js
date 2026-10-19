// The Huntboard popup: log in, read the current tab, show the job for checking, save it.
// For local testing, switch API_URL to "http://127.0.0.1:8000" and add "http://127.0.0.1:8000/*"
// to host_permissions in manifest.json (removed from the published version: reviewers flag unused permissions).
const API_URL = "https://huntboard-api-htbm.onrender.com"
const APP_URL = "https://huntboard.dev"

// Firefox calls the extension API "browser", Chrome calls it "chrome". Same functions, one name here.
const ext = globalThis.browser ?? globalThis.chrome

const $ = (id) => document.getElementById(id)
const show = (id, visible = true) => { $(id).hidden = !visible }

function setStatus(text, { error = false, html = false } = {}) {
  const el = $("status")
  el[html ? "innerHTML" : "textContent"] = text
  el.className = error ? "error" : "muted"
  show("status", Boolean(text))
}

// ---------- the login token, kept in the extension's own storage (not the website's) ----------

async function getToken() {
  return (await ext.storage.local.get("token")).token
}

async function logout() {
  await ext.storage.local.remove("token")
  show("job-view", false)
  show("logout", false)
  setStatus("")
  show("login-view")
}

// fetch with the token. A 401 means the token expired or was revoked (password change): log out.
// The server on Render's free tier may be asleep, so say so if it's slow to answer.
async function api(path, options = {}) {
  const token = await getToken()
  const slow = setTimeout(() => setStatus("Waking up the server… this can take up to a minute."), 5000)
  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: { ...options.headers, Authorization: `Bearer ${token}` },
    })
    if (response.status === 401) {
      await logout()
      setStatus("Your login expired. Log in again.", { error: true })
      throw new Error("logged out")
    }
    return response
  } finally {
    clearTimeout(slow)
  }
}

$("login-view").addEventListener("submit", async (e) => {
  e.preventDefault()
  setStatus("Logging in…")
  try {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      body: new URLSearchParams({ username: $("email").value, password: $("password").value }),
    })
    if (response.status === 403) return setStatus("Verify your email on huntboard.dev first.", { error: true })
    if (!response.ok) return setStatus("Wrong email or password.", { error: true })
    await ext.storage.local.set({ token: (await response.json()).access_token })
    $("password").value = ""
    show("login-view", false)
    readCurrentTab()
  } catch {
    setStatus("Can't reach Huntboard. Check your connection.", { error: true })
  }
})

$("logout").addEventListener("click", logout)

// ---------- reading the page ----------

// This function runs INSIDE the job page (injected by chrome.scripting), not in the popup.
// It only collects raw material; the backend decides what it means.
function collectPage() {
  const jsonLd = []
  for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
    try { jsonLd.push(JSON.parse(script.textContent)) } catch { /* a broken block: skip it */ }
  }
  return {
    url: location.href,
    jsonLd,
    // Capped here so a giant page can't make an oversized request; the backend trims further.
    selection: window.getSelection().toString().slice(0, 50000),
    pageText: (document.body ? document.body.innerText : "").slice(0, 100000),
  }
}

async function readCurrentTab() {
  show("logout")
  setStatus("Reading this page…")
  const [tab] = await ext.tabs.query({ active: true, currentWindow: true })

  let page
  try {
    // activeTab permission: allowed only because you clicked the icon on this tab.
    const [result] = await ext.scripting.executeScript({ target: { tabId: tab.id }, func: collectPage })
    page = result.result
  } catch {
    return setStatus("Your browser doesn't let extensions read this page (browser settings and add-on store pages are protected). Open a job ad and try again.", { error: true })
  }

  try {
    const response = await api("/jobs/parse-page", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(page),
    })
    const body = await response.json().catch(() => ({}))
    if (!response.ok) return setStatus(typeof body.detail === "string" ? body.detail : "Couldn't read this page.", { error: true })
    if (body.alreadySavedJobId) {
      return setStatus(`Already saved. <a href="${APP_URL}/jobs" target="_blank">Open Huntboard</a>`, { html: true })
    }
    fillForm(body)
  } catch (error) {
    if (error.message !== "logged out") setStatus("Can't reach Huntboard. Check your connection.", { error: true })
  }
}

let currentJobUrl = null

function fillForm(job) {
  currentJobUrl = job.jobUrl
  $("company").value = job.companyName ?? ""
  $("role").value = job.jobRole ?? ""
  $("location").value = job.location ?? ""
  $("salary").value = job.salary ?? ""
  $("description").value = job.jobDescription ?? ""
  const sources = { json_ld: "(from the page's structured data)", selection: "(from your selection)", page: "(read by AI)" }
  $("source").textContent = sources[job.source] ?? ""
  // Anything the reader couldn't find is left empty for you to fill in: never a guess.
  setStatus(job.companyName && job.jobRole ? "" : "Some details weren't on the page — please fill them in.")
  show("job-view")
}

// ---------- saving ----------

// Turn a failed save into a reason you can act on, instead of one generic message.
function saveErrorMessage(status, body) {
  if (status >= 500) return "Huntboard had a problem saving this job. Try again in a moment."
  if (Array.isArray(body.detail) && body.detail.length) {     // 422: which field, and why
    const { loc = [], msg = "" } = body.detail[0]
    return `Couldn't save: ${loc.at(-1) ?? "a field"} — ${msg}`
  }
  if (typeof body.detail === "string") return body.detail
  return "Couldn't save this job. Check the details and try again."
}

$("job-view").addEventListener("submit", async (e) => {
  e.preventDefault()
  $("save").disabled = true
  setStatus("Saving… reading the skills")
  try {
    const response = await api("/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        companyName: $("company").value,
        jobRole: $("role").value,
        location: $("location").value,
        salary: $("salary").value,
        jobStatus: $("job-status").value,
        jobDescription: $("description").value,
        jobUrl: currentJobUrl,
      }),
    })
    const body = await response.json().catch(() => ({}))
    if (response.status === 409) {
      show("job-view", false)
      return setStatus(`Already saved. <a href="${APP_URL}/jobs" target="_blank">Open Huntboard</a>`, { html: true })
    }
    if (!response.ok) return setStatus(saveErrorMessage(response.status, body), { error: true })
    show("job-view", false)
    const fit = body.fitScore === null ? "" : ` — ${Math.round(body.fitScore)}% fit`
    setStatus(`Saved ✓${fit}. <a href="${APP_URL}/jobs" target="_blank">Open Huntboard</a>`, { html: true })
  } catch (error) {
    if (error.message !== "logged out") setStatus("Can't reach Huntboard. Check your connection.", { error: true })
  } finally {
    $("save").disabled = false
  }
})

// ---------- permission to reach the API ----------

// Chrome grants host_permissions at install. Firefox treats them as opt-in: the extension must ask,
// and only from a click. Without it, every call to the API would fail.
const API_ORIGINS = { origins: [`${API_URL}/*`] }

async function start() {
  if (!(await ext.permissions.contains(API_ORIGINS))) return show("permission-view")
  show("permission-view", false)
  const token = await getToken()
  token ? readCurrentTab() : show("login-view")
}

$("grant").addEventListener("click", async () => {
  // Must be the first thing the click does: browsers only allow permission prompts straight from a user action.
  const granted = await ext.permissions.request(API_ORIGINS)
  if (granted) start()
  else setStatus("Huntboard needs this permission to save jobs.", { error: true })
})

// ---------- start ----------

start()
