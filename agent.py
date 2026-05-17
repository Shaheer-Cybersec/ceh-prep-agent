#!/usr/bin/env python3
"""
CEH v13 Prep Agent
Practice exams, hands-on lab walkthroughs, and weak-module tracking.
Backend: Groq API (free tier) with local Ollama fallback.
Author: Shaheer Hussain (Shaheer-Cybersec)
"""
import os
import re
import sys
import json
import time
import random
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run: pip install requests")

# ---------- config / env ----------
BASE = Path(__file__).parent
ENV = BASE / ".env"
if ENV.exists():
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

GROQ_KEY = os.environ.get("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
MEM_FILE = BASE / "memory.json"
PASS_LINE = 70  # CEH passing benchmark used for weak-flagging

MODULES = [
    "Introduction to Ethical Hacking",
    "Footprinting and Reconnaissance",
    "Scanning Networks",
    "Enumeration",
    "Vulnerability Analysis",
    "System Hacking",
    "Malware Threats",
    "Sniffing",
    "Social Engineering",
    "Denial-of-Service",
    "Session Hijacking",
    "Evading IDS, Firewalls, and Honeypots",
    "Hacking Web Servers",
    "Hacking Web Applications",
    "SQL Injection",
    "Hacking Wireless Networks",
    "Hacking Mobile Platforms",
    "IoT and OT Hacking",
    "Cloud Computing",
    "Cryptography",
]


# ---------- LLM backend ----------
def llm(prompt, system="You are a strict CEH v13 (AI-Powered) exam expert.", json_mode=True):
    """Call Groq first; fall back to local Ollama. Returns raw text."""
    if GROQ_KEY:
        try:
            body = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.4,
            }
            if json_mode:
                body["response_format"] = {"type": "json_object"}
            r = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_KEY}"},
                json=body,
                timeout=60,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[Groq unavailable: {e} -> trying Ollama]")

    try:
        r = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                "stream": False,
                "format": "json" if json_mode else "",
            },
            timeout=240,
        )
        r.raise_for_status()
        return r.json()["message"]["content"]
    except Exception as e:
        sys.exit(f"No LLM backend. Set GROQ_API_KEY in .env or run Ollama locally. ({e})")


def extract_json(s):
    s = s.strip()
    m = re.search(r"\{.*\}", s, re.S)
    return m.group(0) if m else s


# ---------- memory ----------
def load_mem():
    if MEM_FILE.exists():
        return json.loads(MEM_FILE.read_text())
    return {"modules": {}, "total_q": 0, "total_correct": 0, "history": []}


def save_mem(m):
    MEM_FILE.write_text(json.dumps(m, indent=2))


def record(mem, module, correct, total):
    d = mem["modules"].setdefault(module, {"attempts": 0, "correct": 0})
    d["attempts"] += total
    d["correct"] += correct
    mem["total_q"] += total
    mem["total_correct"] += correct
    mem["history"].append({
        "module": module,
        "score": f"{correct}/{total}",
        "ts": time.strftime("%Y-%m-%d %H:%M"),
    })
    save_mem(mem)


# ---------- features ----------
def gen_questions(module, n):
    prompt = (
        f"Generate {n} CEH v13 exam-style multiple-choice questions for the module "
        f"'{module}'. Make them realistic, scenario-based and tricky. "
        'Return ONLY valid JSON in this shape: '
        '{"questions":[{"q":"text","options":["A ...","B ...","C ...","D ..."],'
        '"answer":"A","explain":"why correct + a relevant tool or command"}]} . '
        "Each option string MUST start with 'A ', 'B ', 'C ' or 'D '."
    )
    data = json.loads(extract_json(llm(prompt)))
    return data["questions"]


def run_quiz(module, n):
    mem = load_mem()
    print(f"\n=== QUIZ: {module}  ({n} questions) ===\n")
    try:
        qs = gen_questions(module, n)
    except Exception as e:
        print(f"Could not generate questions: {e}")
        return
    correct = 0
    for i, q in enumerate(qs, 1):
        print(f"Q{i}. {q['q']}")
        for opt in q["options"]:
            print(f"    {opt}")
        ans = input("Answer (A/B/C/D): ").strip().upper()[:1]
        key = q["answer"].strip().upper()[:1]
        if ans == key:
            print("  [CORRECT]")
            correct += 1
        else:
            print(f"  [WRONG] correct = {key}")
        print(f"  -> {q['explain']}\n")
    record(mem, module, correct, len(qs))
    pct = round(100 * correct / len(qs))
    print(f"=== Score: {correct}/{len(qs)}  ({pct}%) ===")
    if pct < PASS_LINE:
        print(f"[!] Below {PASS_LINE}% pass line -- '{module}' is a weak area.\n")
    else:
        print("[OK] At/above pass line.\n")


def explain(topic):
    prompt = (
        f"Provide a hands-on CEH v13 lab walkthrough for: '{topic}'.\n"
        "Use exactly these sections in plain text (no markdown symbols):\n"
        "OBJECTIVE / TOOLS / STEPS (numbered, with real command syntax) / "
        "EXPECTED OUTPUT / DETECTION & MITIGATION / EXAM TIPS.\n"
        "Be concise, practical and accurate."
    )
    print("\n" + llm(prompt, json_mode=False).strip() + "\n")


def weak(mem):
    scored = [
        (m, d["correct"] / d["attempts"])
        for m, d in mem["modules"].items()
        if d["attempts"] >= 3
    ]
    if not scored:
        print("Not enough data. Complete a few quizzes first (min 3 questions/module).")
        return None
    scored.sort(key=lambda x: x[1])
    print("\n=== WEAKEST MODULES ===")
    for m, acc in scored[:5]:
        print(f"  {round(acc * 100):3}%  {m}")
    return scored[0][0]


def stats(mem):
    print("\n=== PROGRESS DASHBOARD ===")
    if mem["total_q"]:
        ov = round(100 * mem["total_correct"] / mem["total_q"])
        print(f"Overall accuracy : {mem['total_correct']}/{mem['total_q']}  ({ov}%)")
    print(f"Modules attempted: {len(mem['modules'])}/20\n")
    for m, d in sorted(mem["modules"].items()):
        if d["attempts"]:
            print(f"  {round(100 * d['correct'] / d['attempts']):3}%  {m}  ({d['correct']}/{d['attempts']})")
    if mem["history"]:
        print("\nRecent sessions:")
        for h in mem["history"][-5:]:
            print(f"  {h['ts']}  {h['score']:>6}  {h['module']}")
    print()


# ---------- UI ----------
def menu():
    print("""
=========================================
   CEH v13 PREP AGENT
=========================================
  quiz     practice exam on a module
  weak     target your weakest modules
  explain  hands-on lab walkthrough
  stats    progress dashboard
  modules  list all CEH v13 modules
  help     show this menu
  quit     exit
=========================================
""")


def pick_module():
    for i, m in enumerate(MODULES, 1):
        print(f"  {i:2}. {m}")
    c = input("Module number (Enter = random): ").strip()
    if not c:
        return random.choice(MODULES)
    try:
        return MODULES[int(c) - 1]
    except (ValueError, IndexError):
        print("Invalid -> using module 1.")
        return MODULES[0]


def main():
    menu()
    while True:
        try:
            cmd = input("agent> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            return
        mem = load_mem()
        if cmd in ("quit", "exit", "q"):
            print("Bye.")
            return
        elif cmd == "quiz":
            mod = pick_module()
            n = input("Questions (default 5): ").strip()
            run_quiz(mod, int(n) if n.isdigit() and int(n) > 0 else 5)
        elif cmd == "weak":
            w = weak(mem)
            if w and input(f"Quiz on '{w}' now? (y/n): ").strip().lower() == "y":
                run_quiz(w, 5)
        elif cmd == "explain":
            t = input("Topic: ").strip()
            if t:
                explain(t)
        elif cmd == "stats":
            stats(mem)
        elif cmd == "modules":
            for i, m in enumerate(MODULES, 1):
                print(f"  {i:2}. {m}")
        elif cmd in ("help", "menu", ""):
            menu()
        else:
            print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()
