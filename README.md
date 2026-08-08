Sample QUIBL Project

What changed in this repo:
Main.py (modified) - added a second bot instance and four endpoints
review.html (new) - blind side-by-side review page, served by /review
interventions/pledge2/ (new) - 	second bot config, copied from pledge

Difference between the 2 bots:
Only orchestration/prompts.yml is different.
 - four lines changing the audience from parents/guardians to teens
 - guardrails are identitical

Endpoints:

Not changed:
POST /pledge/chat
GET /pledge

Added:
POST /pledge2/chat — chat with the teen-audience. bot
GET /pledge2 — test UI for the other bot
GET /info — both bots bot_info() side by side, including config_hash, safety_hash, quality_hash, and index_collection
POST /compare — sends one message to both bots concurrently, returns both
GET /review — serves review.html

POST /compare
Request body is a standard quibl.AssistantChatRequest. Response:
{
  "config_a": { "bot": "pledge",  "response": { ... } },
  "config_b": { "bot": "pledge2", "response": { ... } }
}

It runs both bots via asyncio.gather(..., return_exceptions=True), so they cant fail each other.

GET /review
Single self contained HTML page. Served from the app itself so the browser calls /compare same-origin.

How it works:
1. Type a question
2. Calls /compare
3. Displays both answers as "Response 1" and "Response 2". IT randomly swapped on every run, so the evaluator can't tell which bot is which
4. Evaluator selects which rubric step decided it, then picks a winner (or tie)
5. Reveals which bot was which
*I wouldn't touch the csv export

