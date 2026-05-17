# PROJECT CONTEXT — CEH v13 Prep Agent
# Keep this file. Paste it into a new Claude chat to resume work without re-explaining.

PROJECT: CEH v13 Prep Agent (Shaheer's portfolio + study tool)
PURPOSE: Free AI agent for CEH v13 exam prep — practice questions, lab walkthroughs, weak-module tracking.

STACK:
- Python 3 CLI (single file: agent.py)
- LLM backend: Groq API free tier, model llama-3.3-70b-versatile (primary)
- Fallback: local Ollama (model llama3.1)
- Persistence: memory.json (per-module accuracy, history)

FILES:
- agent.py            main logic (llm call, quiz engine, explain, weak, stats)
- requirements.txt    requests
- .env.example        GROQ_API_KEY template
- .gitignore          excludes .env + memory.json
- README.md           portfolio-grade docs

KEY DESIGN:
- 20 CEH v13 modules hardcoded in MODULES list
- Quiz: gen_questions() prompts LLM for JSON MCQs, scored vs 70% pass line
- Weak-flagging triggers when module accuracy < 70% and >= 3 attempts
- llm() tries Groq, falls back to Ollama, exits if neither available

DEPLOYMENT TARGET: GitHub repo Shaheer-Cybersec/ceh-prep-agent

POSSIBLE NEXT STEPS (not yet built):
- Streamlit web UI wrapper for a visual portfolio demo
- Export weak-module report to Notion
- Spaced-repetition scheduling on flagged topics
- Flashcard mode reusing existing Anki content

STATUS: v1 complete and syntax-verified. Ready to push to GitHub.
