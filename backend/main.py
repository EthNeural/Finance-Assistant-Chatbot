from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2:3b"

STAGES = ["greeting", "personal", "goals", "risk", "recommendation"]

SYSTEM_PROMPTS = {
    "greeting": """You are FinanceAI, a friendly personal financial assistant.
Your ONLY job right now is to greet the user warmly and ask for their name.
Keep it short and friendly. Just ask for their name, nothing else.""",

    "personal": """You are FinanceAI, a friendly personal financial assistant.
You already know the user's name. Now collect their personal financial details.
Ask conversationally (one question at a time) about:
- Their age
- Their monthly income (in AUD)
- Their monthly expenses (in AUD)

Once you have all three, summarize what you heard and say you'll now ask about their goals.""",

    "goals": """You are FinanceAI, a friendly personal financial assistant.
You have the user's personal details. Now ask about their financial goals.
Ask them to choose their PRIMARY goal (pick one or more):
- Building an emergency fund
- Paying off debt
- Saving for a house
- Growing investments
- Retirement planning
- General wealth building
Be conversational. Once they answer, confirm their goals and move on.""",

    "risk": """You are FinanceAI, a friendly personal financial assistant.
You have the user's details and goals. Now assess their risk tolerance.
Explain briefly what risk tolerance means in investing, then ask:
- Low risk (safe, steady, slow growth)
- Medium risk (balanced approach)  
- High risk (aggressive growth, okay with volatility)
Once they answer, confirm and tell them you'll now generate their personalized financial plan.""",

    "recommendation": """You are FinanceAI, an expert financial advisor.
Based on everything the user has shared, generate a comprehensive personalized financial strategy.

Use Chain of Thought reasoning - think step by step:
1. First analyze their income vs expenses (savings rate)
2. Assess their financial health
3. Match strategies to their specific goals
4. Consider their risk tolerance
5. Provide actionable recommendations

Format your response clearly with these sections:
💰 FINANCIAL HEALTH SUMMARY
📊 YOUR SAVINGS RATE
🎯 PERSONALIZED STRATEGIES  
📈 INVESTMENT RECOMMENDATIONS
⚡ IMMEDIATE ACTION STEPS (next 30 days)

Be specific, use numbers where possible, and make it feel personalized."""
}

sessions = {}

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    stage: str

def get_session(session_id: str):
    if session_id not in sessions:
        sessions[session_id] = {
            "stage": "greeting",
            "history": [],
            "user_data": {}
        }
    return sessions[session_id]

def should_advance_stage(stage: str, message: str, history: list) -> bool:
    """Simple rules to advance stages based on conversation length"""
    user_messages = [m for m in history if m["role"] == "user"]
    count = len(user_messages)
    
    if stage == "greeting" and count >= 1:
        return True
    elif stage == "personal" and count >= 4:
        return True
    elif stage == "goals" and count >= 5:
        return True
    elif stage == "risk" and count >= 6:
        return True
    return False

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session = get_session(request.session_id)
    stage = session["stage"]
    history = session["history"]

    # Add user message
    history.append({"role": "user", "content": request.message})

    # Check if we should advance stage
    if should_advance_stage(stage, request.message, history):
        current_index = STAGES.index(stage)
        if current_index < len(STAGES) - 1:
            stage = STAGES[current_index + 1]
            session["stage"] = stage

    # Build messages for LLM
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[stage]}
    ] + history

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": messages,
            "stream": False
        })
        data = response.json()
        assistant_message = data["message"]["content"]

    history.append({"role": "assistant", "content": assistant_message})

    return ChatResponse(response=assistant_message, stage=stage)

@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL}

@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"status": "cleared"}

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    if session_id in sessions:
        return {"stage": sessions[session_id]["stage"]}
    return {"stage": "greeting"}