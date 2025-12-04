# app.py
import streamlit as st
import pdfplumber
from io import BytesIO
import json
import pandas as pd

st.set_page_config(page_title="Resume Analyzer (Beginner)", layout="centered")

# ---------------- CONFIG ----------------
TEST_MODE = True   # Keep True for now (works locally without any AI key). Set False later when you add Gemini.
MAX_PREVIEW_CHARS = 4000

st.title("Resume Analyzer — Beginner Friendly")
st.write("Upload a PDF resume, preview text, and run a basic AI-style analysis (test mode).")

# ---------------- File upload ----------------
uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

def extract_text_from_pdf_file(file_obj):
    """
    file_obj is a BytesIO or streamlit uploaded file
    Returns extracted text (string)
    """
    text = ""
    try:
        # pdfplumber accepts path or file-like object
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                ptext = page.extract_text()
                if ptext:
                    text += ptext + "\n"
    except Exception as e:
        st.error("Could not extract PDF text. The file may be scanned or image-based.")
        return ""
    return text

# ---------------- Fake AI analysis (for beginners) ----------------
def fake_ai_analyze(resume_text):
    """
    Simple heuristic 'analysis' so you can test without real AI.
    Returns a dict with fields commonly used in resume analyzers.
    """
    # Very simple heuristics — just placeholders
    lower = resume_text.lower()
    skills = []
    common_skills = ["python","java","c++","sql","excel","tensorflow","pandas","numpy","docker","aws"]
    for s in common_skills:
        if s in lower:
            skills.append(s)

    experience_years = 0
    # try to find something like 'X years' - this is very naive
    import re
    m = re.search(r'(\d{1,2})\+?\s+years', resume_text.lower())
    if m:
        experience_years = int(m.group(1))

    summary = "This is a short summary generated in test mode. Replace with real AI later."
    ats_score = min(95, 50 + len(skills) * 5 + (experience_years * 2))

    return {
        "skills": skills,
        "experience_years": experience_years,
        "summary": summary,
        "ats_score": ats_score,
        "improvements": [
            "Add a brief one-line professional summary at the top.",
            "List achievements with metrics (e.g., increased X by Y%)."
        ]
    }

# ---------------- UI and flow ----------------
if uploaded_file:
    # read file bytes into BytesIO for pdfplumber
    bytes_data = uploaded_file.read()
    file_like = BytesIO(bytes_data)

    st.subheader("Document preview (first part)")
    raw_text = extract_text_from_pdf_file(file_like)
    if not raw_text.strip():
        st.warning("No text could be extracted from this PDF. If it's a scanned image, OCR is needed.")
    st.text_area("Extracted text (truncated)", raw_text[:MAX_PREVIEW_CHARS], height=250)

    # Button to analyze
    if st.button("Analyze Resume"):
        st.info("Analyzing resume...")

        if TEST_MODE:
            analysis = fake_ai_analyze(raw_text)
        else:
            # Placeholder for real Gemini call.
            # Implement call_gemini_api() and set TEST_MODE = False to use live AI.
            st.error("TEST_MODE is False but real AI call is not implemented yet.")
            analysis = {}

        # Show results
        st.subheader("Analysis Results")
        st.write("**ATS Score (0-100)**:", analysis.get("ats_score"))
        st.write("**Experience (years)**:", analysis.get("experience_years"))
        st.write("**Skills found**:")
        st.write(", ".join(analysis.get("skills", [])) or "No skills detected by simple heuristics.")
        st.write("**Summary**:")
        st.write(analysis.get("summary"))

        st.write("**Suggested Improvements**")
        for i, it in enumerate(analysis.get("improvements", []), 1):
            st.write(f"{i}. {it}")

        # show structured JSON
        st.subheader("Structured JSON (for developers)")
        st.json(analysis)

else:
    st.info("Upload a resume PDF to begin.")

# Footer help
st.markdown("---")
st.write("If you see blank text extraction, try a different resume PDF (text-based). Scanned PDFs need OCR.")
