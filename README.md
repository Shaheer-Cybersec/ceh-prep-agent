# CEH v13 Prep Agent

A free, terminal-based AI study agent for the **Certified Ethical Hacker v13 (AI-Powered)** exam.
It generates scenario-based practice questions, produces hands-on lab walkthroughs with real
command syntax, tracks performance per module, and auto-flags weak areas for targeted revision.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Backend](https://img.shields.io/badge/LLM-Groq%20%2F%20Ollama-green)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Cost](https://img.shields.io/badge/Cost-Free-success)

## Features

- **Practice exams** — AI-generated MCQs across all 20 CEH v13 modules, scored against the 70% pass line.
- **Lab walkthroughs** — step-by-step hands-on labs with tools, real commands, expected output, and mitigation.
- **Weak-module tracking** — local memory records accuracy per module and surfaces your weakest areas.
- **Progress dashboard** — overall accuracy, per-module breakdown, and recent session history.
- **Dual backend** — runs on the free Groq API, with an offline Ollama fallback. No paid services.

## Architecture

```
agent.py        CLI loop, quiz engine, lab generator
  -> llm()      Groq API (primary)  ->  Ollama localhost (fallback)
  -> memory.json   persistent per-module performance store
```

## Setup

```bash
git clone https://github.com/Shaheer-Cybersec/ceh-prep-agent.git
cd ceh-prep-agent
pip install -r requirements.txt
cp .env.example .env        # then paste your free Groq key into .env
python agent.py
```

Get a free Groq API key at <https://console.groq.com/keys>.

## Usage

| Command   | Action                                    |
|-----------|-------------------------------------------|
| `quiz`    | Practice exam on a chosen/random module   |
| `weak`    | Quiz targeting your lowest-scoring module |
| `explain` | Hands-on lab walkthrough on any topic     |
| `stats`   | Progress dashboard                        |
| `modules` | List all 20 CEH v13 modules               |
| `quit`    | Exit                                      |

## Tech Stack

Python 3 · Groq API (Llama 3.3 70B) · Ollama · JSON persistence

## License

MIT
