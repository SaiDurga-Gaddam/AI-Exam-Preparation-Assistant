
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from groq import Groq
from pypdf import PdfReader


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"

# Always load .env from the project folder
load_dotenv(dotenv_path=ENV_FILE, override=True)

st.set_page_config(
    page_title="AI Exam Preparation Assistant",
    page_icon="📚",
    layout="wide"
)

# Use the current supported Groq model.
# This intentionally does not read GROQ_MODEL from .env.
MODEL_ID = "openai/gpt-oss-120b"


# ==========================================
# 2. GROQ CLIENT
# ==========================================

def get_groq_client():

    api_key = os.getenv("GROQ_API_KEY", "").strip()

    # Remove accidental literal newline characters
    api_key = api_key.replace("\\n", "").replace("\\r", "")

    if not api_key:
        st.error(
            "Groq API key not found. "
            "Please add GROQ_API_KEY to your .env file."
        )
        st.stop()

    return Groq(api_key=api_key)


# ==========================================
# 3. AI GENERATION FUNCTION
# ==========================================

def generate(prompt, system=None):

    if system is None:
        system = (
            "You are a helpful academic tutor. "
            "Explain concepts in simple, clear language. "
            "Use headings, examples and bullet points where useful."
        )

    try:

        groq_client = get_groq_client()

        response = groq_client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {
                    "role": "system",
                    "content": system
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        answer = response.choices[0].message.content

        return answer or "The AI returned an empty response."

    except Exception as e:

        error_message = str(e)

        if "401" in error_message:
            st.error(
                "Authentication failed. Check your Groq API key. "
                "Generate a new key if your old key was revoked."
            )

        elif "404" in error_message or "model_not_found" in error_message:
            st.error(
                f"Model unavailable: {MODEL_ID}. "
                "Check the models available in your Groq account."
            )

        elif "429" in error_message:
            st.error(
                "Groq API rate limit reached. Please wait and try again."
            )

        elif (
            "ConnectError" in error_message
            or "Connection error" in error_message
            or "getaddrinfo failed" in error_message
        ):
            st.error(
                "Unable to connect to Groq. "
                "Check your internet connection, DNS and firewall settings."
            )

        else:
            st.error(f"AI generation failed: {error_message}")

        return None


# ==========================================
# 4. PDF TEXT EXTRACTION
# ==========================================

def read_pdf(uploaded_file):

    reader = PdfReader(uploaded_file)

    extracted_text = []

    for page in reader.pages:

        page_text = page.extract_text() or ""

        if page_text.strip():
            extracted_text.append(page_text)

    return "\n".join(extracted_text).strip()


# ==========================================
# 5. APPLICATION HEADER
# ==========================================

st.title("📚 AI Exam Preparation Assistant")

st.write(
    "Your personal AI-powered study assistant. "
    "Generate study notes, important exam questions, "
    "MCQ quizzes and personalized study timetables."
)

st.caption(f"Powered by Groq AI | Model: {MODEL_ID}")


# ==========================================
# 6. SIDEBAR - STUDY MATERIAL
# ==========================================

with st.sidebar:

    st.header("📖 Study Material")

    st.write(
        "Upload your PDF notes or paste your syllabus "
        "to generate content based on your material."
    )

    uploaded_file = st.file_uploader(
        "Upload a text-based PDF",
        type=["pdf"]
    )

    pasted_text = st.text_area(
        "Or paste syllabus / notes",
        height=200,
        placeholder="Paste your subject notes here..."
    )

    pdf_text = ""

    if uploaded_file is not None:

        try:

            pdf_text = read_pdf(uploaded_file)

            if pdf_text:
                st.success(
                    f"PDF extracted successfully: "
                    f"{len(pdf_text)} characters."
                )
            else:
                st.warning(
                    "No readable text found. "
                    "The PDF may contain scanned images."
                )

        except Exception as e:

            st.error(f"PDF reading error: {e}")

    study_material = (
        pdf_text + "\n" + pasted_text
    ).strip()


# ==========================================
# 7. APPLICATION TABS
# ==========================================

notes_tab, questions_tab, quiz_tab, planner_tab, chat_tab = st.tabs(
    [
        "📝 Notes",
        "❓ Important Questions",
        "🎯 Quiz",
        "📅 Study Planner",
        "💬 Ask My Material"
    ]
)


# ==========================================
# 8. STUDY NOTES GENERATOR
# ==========================================

with notes_tab:

    st.subheader("📝 Generate Study Notes")

    topic = st.text_input(
        "Topic for notes",
        placeholder="e.g. Logistic Regression"
    )

    level = st.selectbox(
        "Select difficulty level",
        [
            "Beginner",
            "College exam",
            "Detailed"
        ]
    )

    if st.button("Generate Notes", key="notes_button"):

        if not topic.strip() and not study_material:

            st.warning(
                "Please enter a topic or upload/paste study material."
            )

        else:

            prompt = f"""
Create {level} study notes on:
{topic or 'the supplied study material'}

Follow this structure:

1. Introduction
2. Definition
3. Explanation of important concepts
4. Working or steps
5. Suitable examples
6. Advantages
7. Disadvantages (where applicable)
8. Important points
9. Short summary

Use simple language suitable for college students.

If study material is provided, use it as the primary source.
Do not invent facts about the supplied material.

STUDY MATERIAL:
{study_material[:18000]}
"""

            with st.spinner("Generating study notes..."):

                result = generate(prompt)

            if result:

                st.markdown("### Generated Study Notes")

                st.markdown(result)

                st.download_button(
                    "⬇️ Download Notes",
                    data=result,
                    file_name="study_notes.md",
                    mime="text/markdown"
                )


# ==========================================
# 9. IMPORTANT EXAM QUESTIONS GENERATOR
# ==========================================

with questions_tab:

    st.subheader("❓ Generate Important Exam Questions")

    question_topic = st.text_input(
        "Subject / Topic",
        placeholder="e.g. Machine Learning"
    )

    marks = st.multiselect(
        "Select marks categories",
        [2, 5, 10],
        default=[2, 5, 10]
    )

    number = st.slider(
        "Questions per category",
        min_value=1,
        max_value=8,
        value=3
    )

    if st.button(
        "Generate Questions",
        key="questions_button"
    ):

        if not question_topic.strip() and not study_material:

            st.warning(
                "Please enter a topic or provide study material."
            )

        elif not marks:

            st.warning("Please select at least one marks category.")

        else:

            prompt = f"""
Generate {number} important exam questions
for each of the following marks categories:

{marks}

Subject / Topic:
{question_topic or 'Based on the supplied study material'}

Organize the questions under separate headings.

Requirements:

- 2-mark questions should test short definitions and concepts.
- 5-mark questions should test explanations and comparisons.
- 10-mark questions should test detailed understanding.
- Avoid unnecessary repetition.
- Keep questions suitable for college examinations.

STUDY MATERIAL:
{study_material[:18000]}
"""

            with st.spinner("Generating important questions..."):

                result = generate(prompt)

            if result:

                st.markdown("### Important Exam Questions")

                st.markdown(result)

                st.download_button(
                    "⬇️ Download Questions",
                    data=result,
                    file_name="important_questions.md",
                    mime="text/markdown"
                )


# ==========================================
# 10. MCQ QUIZ GENERATOR
# ==========================================

with quiz_tab:

    st.subheader("🎯 AI Multiple Choice Quiz")

    quiz_topic = st.text_input(
        "Quiz Topic",
        placeholder="e.g. Machine Learning"
    )

    mcq_count = st.slider(
        "Number of MCQs",
        min_value=3,
        max_value=10,
        value=5
    )

    if st.button("Create Quiz", key="quiz_button"):

        if not quiz_topic.strip() and not study_material:

            st.warning(
                "Please enter a quiz topic or provide study material."
            )

        else:

            prompt = f"""
Create {mcq_count} multiple-choice questions about:

{quiz_topic or 'the supplied study material'}

For each question:

1. Give a clearly numbered question.
2. Provide four options: A, B, C and D.
3. Mention the correct answer.
4. Explain why the answer is correct.

Make the questions suitable for college students.

STUDY MATERIAL:
{study_material[:16000]}
"""

            with st.spinner("Creating your quiz..."):

                result = generate(prompt)

            if result:

                st.session_state["quiz_result"] = result

    if st.session_state.get("quiz_result"):

        st.markdown("### Your Generated Quiz")

        st.markdown(st.session_state["quiz_result"])

        st.download_button(
            "⬇️ Download Quiz",
            data=st.session_state["quiz_result"],
            file_name="practice_quiz.md",
            mime="text/markdown"
        )


# ==========================================
# 11. PERSONALIZED STUDY PLANNER
# ==========================================

with planner_tab:

    st.subheader("📅 Personalized Study Timetable")

    subjects = st.text_input(
        "Subjects (comma-separated)",
        placeholder="Machine Learning, MAD, Python"
    )

    days = st.number_input(
        "Number of days available",
        min_value=1,
        max_value=60,
        value=7
    )

    hours = st.number_input(
        "Study hours per day",
        min_value=1,
        max_value=16,
        value=4
    )

    if st.button(
        "Create Study Plan",
        key="planner_button"
    ):

        if not subjects.strip():

            st.warning("Please enter your subjects.")

        else:

            prompt = f"""
Create a realistic {days}-day study timetable.

Subjects:
{subjects}

Available study time:
{hours} hours per day.

Include:

1. Daily study schedule.
2. Subject-wise time allocation.
3. Short breaks.
4. Revision sessions.
5. Practice questions.
6. Mock tests.
7. Final revision.

Make the schedule practical and balanced.

Format the timetable as a clear Markdown table.
"""

            with st.spinner("Preparing your study timetable..."):

                result = generate(prompt)

            if result:

                st.markdown("### Your Personalized Study Plan")

                st.markdown(result)

                st.download_button(
                    "⬇️ Download Study Plan",
                    data=result,
                    file_name="study_plan.md",
                    mime="text/markdown"
                )


# ==========================================
# 12. ASK MY STUDY MATERIAL
# ==========================================

with chat_tab:

    st.subheader("💬 Ask Questions From Your Study Material")

    st.write(
        "Ask questions about your uploaded PDF "
        "or pasted subject notes."
    )

    user_question = st.text_input(
        "Enter your question",
        placeholder="e.g. Explain Logistic Regression"
    )

    if st.button(
        "Ask Material",
        key="chat_button"
    ):

        if not study_material:

            st.warning(
                "Please upload a PDF or paste your notes in the sidebar."
            )

        elif not user_question.strip():

            st.warning("Please enter a question.")

        else:

            prompt = f"""
Answer the following question using ONLY the
provided study material.

If the answer is not present in the material,
clearly mention that.

Explain the answer in simple language.
Use headings and bullet points where appropriate.

STUDY MATERIAL:
{study_material[:22000]}

QUESTION:
{user_question}
"""

            with st.spinner("Finding your answer..."):

                result = generate(prompt)

            if result:

                st.markdown("### Answer")

                st.markdown(result)


# ==========================================
# 13. FOOTER
# ==========================================

st.divider()

st.caption(
    "📚 AI Exam Preparation Assistant | "
    "Powered by Python, Streamlit and Groq AI. "
    "Educational support only. "
    "Verify important content with your syllabus and instructor."
)
