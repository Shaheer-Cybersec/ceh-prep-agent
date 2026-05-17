#!/usr/bin/env python3
"""
CEH v13 Prep Agent - Web GUI (Streamlit)
Reuses the backend in agent.py. Run locally:  streamlit run app.py
"""
import os
import streamlit as st

# Inject Streamlit Cloud secret into env BEFORE importing agent
# (agent.py reads GROQ_API_KEY at import time).
try:
    if "GROQ_API_KEY" in st.secrets:
        os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
except Exception:
    pass

import agent  # noqa: E402

st.set_page_config(page_title="CEH v13 Prep Agent", page_icon="🛡", layout="wide")

PASS = agent.PASS_LINE


def backend_label():
    return f"Groq · {agent.GROQ_MODEL}" if agent.GROQ_KEY else f"Ollama · {agent.OLLAMA_MODEL}"


# ---------- sidebar ----------
with st.sidebar:
    st.title("🛡 CEH v13 Prep Agent")
    st.caption(f"Backend: {backend_label()}")
    page = st.radio("Navigate", ["Practice Quiz", "Lab Walkthrough", "Weak Modules", "Progress"])
    st.divider()
    _m = agent.load_mem()
    if _m["total_q"]:
        st.metric("Overall accuracy", f"{round(100 * _m['total_correct'] / _m['total_q'])}%")
    st.metric("Modules attempted", f"{len(_m['modules'])}/20")
    st.caption("AI-powered CEH v13 exam prep. Free backend.")


# ---------- Practice Quiz ----------
if page == "Practice Quiz":
    st.title("Practice Quiz")
    c1, c2, c3 = st.columns([3, 1, 1])
    module = c1.selectbox("Module", agent.MODULES)
    n = c2.number_input("Questions", 3, 15, 5)
    c3.write("")
    c3.write("")
    if c3.button("Generate", type="primary", use_container_width=True):
        with st.spinner("Generating CEH-style questions..."):
            try:
                st.session_state.qs = agent.gen_questions(module, int(n))
                st.session_state.qmod = module
                st.session_state.submitted = False
                st.session_state.recorded = False
            except Exception as e:
                st.session_state.qs = None
                st.error(f"Generation failed: {e}")

    qs = st.session_state.get("qs")
    if qs:
        st.divider()
        submitted = st.session_state.get("submitted", False)
        picks = []
        for i, q in enumerate(qs):
            st.markdown(f"**Q{i + 1}. {q['q']}**")
            p = st.radio(
                "options", q["options"], index=None, key=f"ans_{i}",
                label_visibility="collapsed", disabled=submitted,
            )
            picks.append(p)
            st.write("")

        if not submitted:
            if st.button("Submit Answers", type="primary"):
                st.session_state.submitted = True
                st.rerun()
        else:
            correct = 0
            for i, q in enumerate(qs):
                picked = (picks[i] or "")[:1].upper()
                key = q["answer"].strip().upper()[:1]
                ok = picked == key
                correct += int(ok)
                with st.expander(f"Q{i + 1}:  {'Correct' if ok else 'Wrong'}", expanded=not ok):
                    st.write(f"Your answer: {picks[i] or '(none)'}")
                    st.write(f"Correct answer: {key}")
                    st.info(q["explain"])
            total = len(qs)
            pct = round(100 * correct / total)
            if not st.session_state.get("recorded"):
                m = agent.load_mem()
                agent.record(m, st.session_state.qmod, correct, total)
                st.session_state.recorded = True
            st.metric(f"Score — {st.session_state.qmod}", f"{correct}/{total}  ({pct}%)")
            if pct < PASS:
                st.warning(f"Below the {PASS}% pass line — flagged as a weak area.")
            else:
                st.success("At or above the pass line.")


# ---------- Lab Walkthrough ----------
elif page == "Lab Walkthrough":
    st.title("Lab Walkthrough")
    st.caption("Hands-on lab with tools, real commands, expected output and mitigation.")
    topic = st.text_input("Topic", placeholder="e.g. SMB enumeration with enum4linux")
    if st.button("Generate Walkthrough", type="primary") and topic:
        prompt = (
            f"Provide a hands-on CEH v13 lab walkthrough for: '{topic}'.\n"
            "Use these sections: OBJECTIVE / TOOLS / STEPS (numbered, with real "
            "command syntax) / EXPECTED OUTPUT / DETECTION & MITIGATION / EXAM TIPS.\n"
            "Be concise, practical and accurate."
        )
        with st.spinner("Building lab..."):
            try:
                st.markdown(agent.llm(prompt, json_mode=False))
            except Exception as e:
                st.error(f"Failed: {e}")


# ---------- Weak Modules ----------
elif page == "Weak Modules":
    st.title("Weak Modules")
    mem = agent.load_mem()
    scored = [
        (m, d["correct"] / d["attempts"])
        for m, d in mem["modules"].items()
        if d["attempts"] >= 3
    ]
    if not scored:
        st.info("Complete a few quizzes first (minimum 3 questions per module).")
    else:
        scored.sort(key=lambda x: x[1])
        st.caption("Lowest accuracy first. Drill these in the Practice Quiz tab.")
        for m, acc in scored[:8]:
            st.write(f"**{m}** — {round(acc * 100)}%")
            st.progress(acc)


# ---------- Progress ----------
elif page == "Progress":
    st.title("Progress Dashboard")
    mem = agent.load_mem()
    c1, c2, c3 = st.columns(3)
    ov = round(100 * mem["total_correct"] / mem["total_q"]) if mem["total_q"] else 0
    c1.metric("Overall accuracy", f"{ov}%")
    c2.metric("Questions answered", mem["total_q"])
    c3.metric("Modules attempted", f"{len(mem['modules'])}/20")
    st.divider()
    st.subheader("Per-module accuracy")
    any_data = False
    for m in agent.MODULES:
        d = mem["modules"].get(m)
        if d and d["attempts"]:
            any_data = True
            acc = d["correct"] / d["attempts"]
            st.write(f"{m} — {round(acc * 100)}%  ({d['correct']}/{d['attempts']})")
            st.progress(acc)
    if not any_data:
        st.info("No quiz data yet. Take a quiz to populate this dashboard.")
    if mem["history"]:
        st.subheader("Recent sessions")
        for h in reversed(mem["history"][-8:]):
            st.text(f"{h['ts']}   {h['score']:>6}   {h['module']}")
