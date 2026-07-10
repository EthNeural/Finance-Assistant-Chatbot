# FinanceAI — Conversational Financial Planning Assistant

FinanceAI is a full-stack conversational assistant that walks a user through a structured financial planning conversation and produces a personalised, Chain-of-Thought financial strategy. It runs entirely on a local LLM via Ollama, so no external API keys or cloud inference are required.

## How it works

The assistant guides the user through five conversation stages, each with its own system prompt, and advances automatically as enough information is collected:

1. **Greeting** — introduces itself and asks for the user's name
2. **Personal** — collects age, monthly income, and monthly expenses (AUD)
3. **Goals** — asks the user to choose their primary financial goal(s): emergency fund, debt payoff, house deposit, investing, retirement, or general wealth building
4. **Risk** — assesses risk tolerance (low / medium / high) with a brief explanation of what that means for investing
5. **Recommendation** — generates the final strategy using explicit Chain-of-Thought reasoning: analyse savings rate → assess financial health → match strategies to goals → factor in risk tolerance → give concrete next steps. Output is formatted into clear sections (financial health summary, savings rate, personalised strategies, investment recommendations, and a 30-day action plan).

Each conversation is tracked by session ID with an in-memory history and stage tracker, so the assistant always knows where the user is in the flow.

## Architecture

- **Backend** (`backend/`) — FastAPI service that maintains per-session conversation state and forwards the staged system prompt + message history to a local Ollama instance (`llama3.2:3b`) for each turn. Exposes `/chat`, `/health`, and session management endpoints.
- **Frontend** (`frontend/`) — React chat interface (dark theme, Tailwind-style utility classes) with a typing indicator, auto-scroll, and a "New Chat" reset that clears the session on the backend.
- **Model selection notebook** (`notebook/comparision.ipynb`) — benchmarks three local models on the same financial-planning prompt: Llama 3.2 (3B), Gemma 2 (2B), and Phi 3 Mini, comparing response time and word count. Llama 3.2 was selected for the backend as the best balance of speed and detail, including picking up Australia-specific context (e.g. Superannuation) unprompted.
- **Project report** (`FinanceAI_Report.pdf`) — full write-up of the project.

## Tech stack

FastAPI, httpx, Ollama (local LLM inference), React, prompt-engineered Chain-of-Thought reasoning.

## Status

This is a local prototype: the backend expects Ollama running on `localhost:11434`, session state is in-memory (not persisted), and CORS is scoped to `localhost:3000`. Productionising would involve persistent session storage, environment-configurable endpoints, and auth.

## Running locally

1. Install and run [Ollama](https://ollama.com), then pull the model: `ollama pull llama3.2:3b`
2. Backend: `cd backend && pip install fastapi uvicorn httpx && uvicorn main:app --reload`
3. Frontend: `cd frontend` and run with your preferred React setup (Create React App / Vite), pointing at `http://localhost:8000`
