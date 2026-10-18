# Job Application Tracker

## Who writes what

The goal of this project is to learn the AI core deeply. AI builds the application around it; I write the parts I need to explain in depth in interviews.

### AI may write
- CSS and Tailwind styling, layout, and visual appearance
- React components, pages, forms, and wiring the UI to existing API endpoints
- FastAPI setup, routes, and CRUD endpoints for non-AI data
- Database models, Alembic migrations, and CRUD queries
- Authentication (following FastAPI's official security tutorial)
- Configuration, environment setup, Docker, deployment, and CI
- Tests for code that AI wrote

### AI must NOT write
- Scoring and gap logic: fit score, missing skills, and frequency counting, plus their tests
- AI extraction: prompts, LLM API calls, Pydantic schemas for AI output, skill-name normalisation, and failure/retry handling
- RAG: chunking, embeddings, similarity search queries, reranking, answer generation, and citations
- Evaluation: golden datasets, metrics, and eval scripts
- Any other prompts, agents, or AI functionality

For anything in the list above, AI may explain concepts, suggest approaches, or review code that I write, but I will write the implementation myself.

### Exception: Section 8c (browser extension), decided 2026-10-18
- AI may write all of 8c, including the job-posting extraction (prompt, Pydantic schema, LLM call, retry handling), field normalisation, and the evaluation.
- In return, AI walks me through the core logic in depth before I commit, and I must be able to explain it: the extraction prompt and schema, the JSON-LD → selection → page-text fallback, the needs-review rule, and how the eval scores precision and recall.
- The golden pages and their expected answers (backend/tests/fixtures/pages/) stay mine to collect and write.
- Everything outside 8c keeps the rules above.

## Understanding what AI writes

- Explain every non-obvious decision in plain terms, especially database schema (keys, relationships), joins, transactions, async code, and auth flow.
- When AI writes code that uses a concept I haven't learned yet, name the concept so I can study it.
- I must be able to explain any file before it's committed. If I can't, AI walks me through it before we move on.

## How AI changes are checked

- Keep each AI change small enough for me to review in one sitting.
- AI must not make large, unrelated changes.
- I will review all AI-generated code before it is used or committed.
- AI must not commit changes, create commits, or push to the repository.
- I am responsible for reviewing `git diff` and deciding whether changes should be kept.
- I write all commit messages and make all commits myself.
