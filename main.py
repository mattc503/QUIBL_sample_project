import asyncio
import os
from pathlib import Path

import quibl
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI()
here = Path(__file__).resolve().parent


"""
To instantiate quibl bot, supply:
path, 
optional retrieval store path (where the vector db persists), 
credentials.
"""
pledge_bot = quibl.InterventionBot(
    here / "interventions" / "pledge",
    retrieval_store_path=os.getenv("QUIBL_RETRIEVAL_STORE_PATH", "/data/quibl/chroma"),
    credentials={"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")},
)

# Second bot: same guardrails, different config directory (interventions/pledge2)
pledge2_bot = quibl.InterventionBot(
    here / "interventions" / "pledge2",
    retrieval_store_path=os.getenv("QUIBL_RETRIEVAL_STORE_PATH_2", "/data/quibl/chroma_pledge2"),
    credentials={"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")},
)


# Chat endpoint
@app.post("/pledge/chat")
async def pledge_chat(req: quibl.AssistantChatRequest):
    try:
        return await pledge_bot.chat(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Test web view for profiling the bot. Navigate to localhost:8000/pledge
@app.get("/pledge", response_class=HTMLResponse)
def pledge_index():
    return HTMLResponse(
        quibl.render_test_ui_html(
            intervention_id="pledge",
            title="PLEDGE",
            chat_endpoint="/pledge/chat",
            bot_info=pledge_bot.bot_info(),
        )
    )


# Chat endpoint for the second bot
@app.post("/pledge2/chat")
async def pledge2_chat(req: quibl.AssistantChatRequest):
    try:
        return await pledge2_bot.chat(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Test web view for the second bot. Navigate to localhost:8000/pledge2
@app.get("/pledge2", response_class=HTMLResponse)
def pledge2_index():
    return HTMLResponse(
        quibl.render_test_ui_html(
            intervention_id="pledge2",
            title="PLEDGE for Teens",
            chat_endpoint="/pledge2/chat",
            bot_info=pledge2_bot.bot_info(),
        )
    )


# Dumps what each bot reports about itself, including config hashes, so you can
# see which hash moves when you edit a config file. Navigate to localhost:8000/info
@app.get("/info")
def info():
    return {
        "pledge": pledge_bot.bot_info(),
        "pledge2": pledge2_bot.bot_info(),
    }


# Blind side by side review page. Navigate to localhost:8000/review
# Served from the app itself so the browser can call /compare without CORS issues.
@app.get("/review", response_class=HTMLResponse)
def review_page():
    return HTMLResponse((here / "review.html").read_text())


# Sends the same question to both configs at once, for side by side A/B review.
# Only a fair quality comparison if the two configs share the same guardrails
# and differ on the RAG / orchestration side, since quality iteration is meant
# to hold guardrails invariant.
@app.post("/compare")
async def compare(req: quibl.AssistantChatRequest):
    a_result, b_result = await asyncio.gather(
        pledge_bot.chat(req),
        pledge2_bot.chat(req),
        return_exceptions=True,
    )

    def _serialize(label, result):
        if isinstance(result, Exception):
            return {"bot": label, "error": str(result)}
        return {"bot": label, "response": result}

    return {
        "config_a": _serialize("pledge", a_result),
        "config_b": _serialize("pledge2", b_result),
    }
