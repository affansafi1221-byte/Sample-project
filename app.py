"""InsightForge - Streamlit dashboard. Run: streamlit run app.py"""
import os, shutil
import streamlit as st

from state import new_state, save_state, list_sessions, load_state, SESSIONS_DIR
from llm import LLMClient
from orchestrator import run_session

st.set_page_config(page_title="InsightForge", page_icon="🛠️", layout="wide")
st.title("🛠️ InsightForge — Agentic Data Analyst")
st.caption("Planner → Analyst → Critic → Reporter, with sandboxed execution and a live reasoning trace")

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("⚙️ Configuration")
    mode = st.radio("LLM mode", ["Demo mode (no API key)", "Claude API"], index=0)
    api_key, model = "", "claude-3-5-haiku-latest"
    if mode == "Claude API":
        api_key = st.text_input("ANTHROPIC_API_KEY", type="password")
        model = st.selectbox("Model", ["claude-3-5-haiku-latest", "claude-3-5-sonnet-latest", "claude-3-7-sonnet-latest"])
    st.divider()
    uploaded = st.file_uploader("Upload CSV dataset", type=["csv"])
    goal = st.text_area("Analysis goal",
        value="Find the main drivers of revenue and flag data-quality risks before building a forecasting model.")
    run_clicked = st.button("🚀 Run agent session", type="primary", disabled=uploaded is None)
    st.divider()
    st.header("📁 Past sessions")
    for sid in list_sessions()[:8]:
        if st.button(sid, key=f"load_{sid}"):
            st.session_state["result"] = load_state(sid)

# ---------------- Run ----------------
if run_clicked and uploaded:
    work = os.path.join(SESSIONS_DIR, "_upload_tmp")
    os.makedirs(work, exist_ok=True)
    data_path = os.path.join(work, "data.csv")
    with open(data_path, "wb") as f:
        f.write(uploaded.getbuffer())

    llm = LLMClient(mode="api" if mode == "Claude API" else "mock", model=model, api_key=api_key)
    state = new_state(data_path, goal)
    # move dataset into the session workdir so the sandbox runs in a clean folder
    final_path = os.path.join(state["workdir"], "data.csv")
    shutil.copy(data_path, final_path)
    state["dataset_path"] = final_path

    log = st.empty()
    log_lines = []
    def cb(msg):
        log_lines.append(msg)
        log.write("\n".join(log_lines))

    with st.spinner("Agents working..."):
        state = run_session(state, llm=llm, cb=cb)
    st.session_state["result"] = state
    st.success(f"Session {state['session_id']} finished with status: {state['status']}")

# ---------------- Results ----------------
result = st.session_state.get("result")
if result:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Status", result["status"])
    c2.metric("Plan steps", len(result["plan"]))
    c3.metric("Attempts", len(result["code_history"]))
    c4.metric("Verified findings", len(result["findings"]))

    with st.expander("🧭 Plan", expanded=True):
        for s in result["plan"]:
            st.write(("✅" if s.get("done") else "⬜"), f"**Step {s['id']}** — {s['instruction']}")

    with st.expander("⚙️ Code history (reasoning trace)"):
        for a in result["code_history"]:
            ok = a["success"]
            st.write(f"**Step {a['step']} · attempt {a['attempt_no']}** — {'✅' if ok else '❌'}")
            st.code(a["code"], language="python")
            if a["stdout"]:
                st.text(a["stdout"][:1500])
            if a["stderr"]:
                st.error(a["stderr"][:500])

    with st.expander("🔎 Verified findings"):
        for f in result["findings"]:
            st.markdown(f"**Step {f['step']}:** {f['instruction']}")
            st.text(f["evidence"])

    if result.get("report_md"):
        with st.expander("📄 Report", expanded=True):
            st.markdown(result["report_md"])
        st.download_button("⬇️ Download report.md", result["report_md"], file_name="insightforge_report.md")
else:
    st.info("Upload a CSV and press **Run agent session**. Demo mode works with no API key.")
    st.markdown("""**Tip for a strong demo:** use a messy dataset — missing values, weird dtypes, a categorical
column in a numeric context — so the retry/self-correction loop visibly activates.""")
