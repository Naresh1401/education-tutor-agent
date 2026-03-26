"""
Streamlit Dashboard — Interactive frontend for the AI Education Tutor Agent.
"""

import os
import json
import asyncio

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Education Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy Agent Initialization ─────────────────────────────────────


@st.cache_resource
def load_agents():
    from src.agents.socratic_tutor import SocraticTutor
    from src.agents.concept_explainer import ConceptExplainer
    from src.agents.quiz_generator import QuizGenerator
    from src.agents.learning_path_planner import LearningPathPlanner
    from src.agents.progress_tracker import ProgressTracker

    return {
        "tutor": SocraticTutor(),
        "explainer": ConceptExplainer(),
        "quiz": QuizGenerator(),
        "planner": LearningPathPlanner(),
        "progress": ProgressTracker(),
    }


def run_async(coro):
    """Run an async coroutine from synchronous Streamlit code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Session State Defaults ─────────────────────────────────────────

if "student_id" not in st.session_state:
    st.session_state.student_id = "student_01"
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "quiz_results" not in st.session_state:
    st.session_state.quiz_results = []

# ── Sidebar ────────────────────────────────────────────────────────

SUBJECTS = {
    "Mathematics": {"key": "math", "topics": ["Algebra", "Calculus", "Linear Algebra", "Statistics"]},
    "Computer Science": {"key": "cs", "topics": ["Data Structures", "Algorithms", "OOP", "Databases"]},
    "Science": {"key": "science", "topics": ["Physics", "Chemistry", "Biology"]},
    "History": {"key": "history", "topics": ["World History", "US History", "Ancient Civilizations"]},
}

with st.sidebar:
    st.title("🎓 AI Education Tutor")
    st.markdown("---")

    st.session_state.student_id = st.text_input("Student ID", value=st.session_state.student_id)

    selected_subject = st.selectbox("Subject", list(SUBJECTS.keys()))
    subject_info = SUBJECTS[selected_subject]
    selected_topic = st.selectbox("Topic", subject_info["topics"])

    st.markdown("---")
    mode = st.radio(
        "Mode",
        ["💬 Socratic Tutor", "📚 Concept Explorer", "📝 Quiz Mode", "🗺️ Learning Path", "📊 Progress"],
        index=0,
    )

    st.markdown("---")
    st.caption("Built with LangChain + LangGraph")

# ── Main Content ───────────────────────────────────────────────────

agents = load_agents()

# ── Socratic Tutor Mode ───────────────────────────────────────────

if mode == "💬 Socratic Tutor":
    st.header("💬 Socratic Tutor")
    st.caption(f"Subject: {selected_subject} | Topic: {selected_topic}")
    st.info("The tutor will guide you through questions — it won't give direct answers!")

    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Ask a question or share your thinking..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = run_async(agents["tutor"].ask(
                    student_message=user_input,
                    student_id=st.session_state.student_id,
                    subject=subject_info["key"],
                    topic=selected_topic.lower(),
                ))
            st.markdown(result["response"])

            with st.expander("Session Info"):
                st.json({
                    "level": result["student_level"],
                    "misconceptions": result["misconceptions"],
                    "questions_exchanged": result["question_count"],
                })

        st.session_state.chat_history.append({"role": "assistant", "content": result["response"]})

    if st.sidebar.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

# ── Concept Explorer Mode ─────────────────────────────────────────

elif mode == "📚 Concept Explorer":
    st.header("📚 Concept Explorer")
    st.caption(f"Subject: {selected_subject} | Topic: {selected_topic}")

    concept = st.text_input("Enter a concept to explore:", placeholder="e.g., Quadratic equations, Binary search trees...")

    level_col1, level_col2 = st.columns([1, 3])
    with level_col1:
        level = st.selectbox("Explanation Level", ["Auto-detect", "Beginner (ELI5)", "Intermediate", "Advanced"])

    level_map = {
        "Auto-detect": None,
        "Beginner (ELI5)": "beginner",
        "Intermediate": "intermediate",
        "Advanced": "advanced",
    }

    if st.button("Explain", type="primary") and concept:
        with st.spinner("Generating explanation..."):
            result = run_async(agents["explainer"].explain(
                concept=concept,
                subject=subject_info["key"],
                level=level_map[level],
            ))
        st.success(f"Level: **{result['level'].title()}**")
        st.markdown(result["explanation"])

    st.markdown("---")
    if st.checkbox("Compare all levels"):
        if concept:
            with st.spinner("Generating all levels..."):
                result = run_async(agents["explainer"].explain_all_levels(
                    concept=concept,
                    subject=subject_info["key"],
                ))
            tabs = st.tabs(["🟢 Beginner", "🟡 Intermediate", "🔴 Advanced"])
            for tab, (lvl, text) in zip(tabs, result["explanations"].items()):
                with tab:
                    st.markdown(text)

# ── Quiz Mode ─────────────────────────────────────────────────────

elif mode == "📝 Quiz Mode":
    st.header("📝 Adaptive Quiz")
    st.caption(f"Subject: {selected_subject} | Topic: {selected_topic}")

    col1, col2, col3 = st.columns(3)
    with col1:
        num_q = st.number_input("Questions", min_value=1, max_value=15, value=5)
    with col2:
        q_types = st.multiselect(
            "Question Types",
            ["multiple_choice", "fill_in_blank", "short_answer", "coding"],
            default=["multiple_choice", "short_answer"],
        )
    with col3:
        adaptive = st.checkbox("Adaptive Difficulty", value=True)

    if st.button("Generate Quiz", type="primary"):
        from src.agents.quiz_generator import QuizConfig
        config = QuizConfig(
            subject=subject_info["key"],
            topic=selected_topic.lower(),
            num_questions=num_q,
            question_types=q_types,
        )
        with st.spinner("Generating quiz..."):
            quiz = run_async(agents["quiz"].generate_quiz(
                config=config,
                student_id=st.session_state.student_id,
                adaptive=adaptive,
            ))
        st.session_state.quiz_questions = quiz.get("questions", [])
        st.session_state.quiz_index = 0
        st.session_state.quiz_results = []

    # Display quiz questions
    questions = st.session_state.quiz_questions
    if questions:
        idx = st.session_state.quiz_index
        if idx < len(questions):
            q = questions[idx]
            st.subheader(f"Question {idx + 1} of {len(questions)}")
            st.markdown(f"**Type:** {q.get('type', 'N/A')} | **Difficulty:** {'⭐' * q.get('difficulty', 1)}")
            st.markdown(q.get("question", ""))

            if q.get("type") == "multiple_choice" and q.get("options"):
                answer = st.radio("Your answer:", q["options"], key=f"q_{idx}")
            else:
                answer = st.text_area("Your answer:", key=f"q_{idx}")

            if st.button("Submit Answer"):
                with st.spinner("Evaluating..."):
                    result = run_async(agents["quiz"].evaluate_answer(
                        question=q,
                        student_answer=answer,
                        student_id=st.session_state.student_id,
                    ))
                st.session_state.quiz_results.append(result)

                if result.get("is_correct"):
                    st.success("Correct! ✅")
                else:
                    st.error("Not quite. ❌")
                st.markdown(f"**Feedback:** {result.get('feedback', '')}")

                if result.get("misconception"):
                    st.warning(f"📌 Misconception detected: {result['misconception']}")

                st.session_state.quiz_index += 1
                st.rerun()
        else:
            st.success("Quiz complete!")
            results = st.session_state.quiz_results
            correct = sum(1 for r in results if r.get("is_correct"))
            st.metric("Score", f"{correct}/{len(results)}", f"{correct/len(results)*100:.0f}%")

            with st.expander("Detailed Results"):
                for i, r in enumerate(results):
                    icon = "✅" if r.get("is_correct") else "❌"
                    st.markdown(f"{icon} **Q{i+1}**: {r.get('feedback', '')}")

# ── Learning Path Mode ────────────────────────────────────────────

elif mode == "🗺️ Learning Path":
    st.header("🗺️ Personalized Learning Path")
    st.caption(f"Subject: {selected_subject}")

    target = st.selectbox("Target topic to learn:", subject_info["topics"])

    st.markdown("**Your current knowledge** (0 = none, 1 = mastered):")
    knowledge = {}
    cols = st.columns(min(len(subject_info["topics"]), 4))
    for i, topic in enumerate(subject_info["topics"]):
        with cols[i % len(cols)]:
            knowledge[topic.lower()] = st.slider(topic, 0.0, 1.0, 0.3, 0.1, key=f"k_{topic}")

    if st.button("Generate Learning Path", type="primary"):
        from src.agents.learning_path_planner import LearningPathConfig
        config = LearningPathConfig(
            student_id=st.session_state.student_id,
            subject=subject_info["key"],
            target_topic=target.lower(),
            current_knowledge=knowledge,
        )
        with st.spinner("Planning your path..."):
            result = run_async(agents["planner"].create_learning_path(config))

        st.subheader("Your Learning Path")

        if result.get("gaps"):
            st.warning(f"📌 Knowledge gaps identified: {', '.join(result['gaps'])}")

        path = result.get("learning_path", {})
        steps = path.get("path", [])
        if steps:
            for i, step in enumerate(steps, 1):
                priority = step.get("priority", "required")
                icon = {"required": "🔴", "recommended": "🟡", "optional": "🟢"}.get(priority, "⚪")
                with st.expander(f"{icon} Step {i}: {step.get('topic', 'N/A')} ({priority})"):
                    st.markdown(f"**Estimated time:** {step.get('estimated_hours', '?')} hours")
                    st.markdown(f"**Reason:** {step.get('reason', '')}")
                    objectives = step.get("learning_objectives", [])
                    if objectives:
                        st.markdown("**Objectives:**")
                        for obj in objectives:
                            st.markdown(f"- {obj}")

            total = path.get("total_estimated_hours", 0)
            st.info(f"📅 Total estimated time: **{total} hours**")

        recs = path.get("recommendations", [])
        if recs:
            st.subheader("Recommendations")
            for rec in recs:
                st.markdown(f"- {rec}")

# ── Progress Dashboard ────────────────────────────────────────────

elif mode == "📊 Progress":
    st.header("📊 Progress Dashboard")
    st.caption(f"Student: {st.session_state.student_id}")

    tracker = agents["progress"]
    student_data = tracker.get_all_progress(st.session_state.student_id)

    if not student_data or not student_data.get("topics"):
        st.info("No progress data yet. Complete some quizzes or tutoring sessions to see your progress!")
    else:
        # Mastery overview
        st.subheader("Topic Mastery")
        topics = student_data["topics"]
        mastery_data = {t: info["mastery_score"] for t, info in topics.items()}

        col1, col2 = st.columns(2)
        with col1:
            st.bar_chart(mastery_data)
        with col2:
            sw = tracker.get_strengths_weaknesses(st.session_state.student_id)
            if sw["strengths"]:
                st.markdown("**💪 Strengths:**")
                for s in sw["strengths"]:
                    st.markdown(f"- {s['topic']}: {s['mastery']:.0%}")
            if sw["weaknesses"]:
                st.markdown("**📈 Areas to Improve:**")
                for w in sw["weaknesses"]:
                    st.markdown(f"- {w['topic']}: {w['mastery']:.0%}")

        # Velocity
        st.subheader("Learning Velocity")
        velocity = tracker.get_learning_velocity(st.session_state.student_id)
        v_col1, v_col2, v_col3 = st.columns(3)
        v_col1.metric("Topics Mastered", velocity["topics_mastered"])
        v_col2.metric("Velocity", f"{velocity['velocity']}/week")
        v_col3.metric("Trend", velocity["trend"].replace("_", " ").title())

        # Time analytics
        st.subheader("Time Analytics")
        time_data = tracker.get_time_analytics(st.session_state.student_id)
        st.metric("Total Study Time", f"{time_data['total_minutes']:.0f} min")
        if time_data["per_topic"]:
            time_chart = {t: v["minutes"] for t, v in time_data["per_topic"].items()}
            st.bar_chart(time_chart)

        # AI report
        if st.button("Generate AI Progress Report"):
            with st.spinner("Analyzing your progress..."):
                report = run_async(tracker.generate_report(
                    st.session_state.student_id,
                    subject_info["key"],
                ))
            st.markdown(report.get("report", "No report available."))
