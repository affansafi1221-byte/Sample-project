"""The agentic loop: Planner -> Analyst -> Critic -> (retry | next step) -> Reporter."""
from state import save_state
from agents import planner, analyst, critic, reporter


def run_session(state, llm=None, cb=None):
    cb = cb or (lambda msg: None)

    state = planner.plan(state, llm)
    cb(f"🧭 Planner proposed {len(state['plan'])} step(s)")
    save_state(state)

    while True:
        if all(s.get("done") for s in state["plan"]):
            state["status"] = "reporting"
            break
        if state["retry_count"] >= state["max_retries"]:
            state["status"] = "escalated"
            cb("🚨 Escalated to human after max retries")
            break

        state = analyst.execute_next_step(state, llm)
        attempt = state["code_history"][-1]
        cb(f"⚙️ Analyst ran step {attempt['step']} "
           f"({'success' if attempt['success'] else 'error'})")

        state = critic.verify(state, llm)
        if state["status"] == "verified":
            cb(f"✅ Critic verified step {attempt['step']}")
        elif state["status"] == "needs_fix":
            note = state.get("last_critic_note", "")[:100]
            cb(f"🔁 Critic rejected step {attempt['step']} (retry "
               f"{state['retry_count']}/{state['max_retries']}): {note}")
        save_state(state)

    if state["status"] == "reporting":
        state = reporter.generate(state, llm)
        cb(f"📄 Report written to {state['report_path']}")
        save_state(state)
    return state
