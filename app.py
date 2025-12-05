import streamlit as st
import pdfplumber
from io import BytesIO
import json
import requests
import time

# ---------------- CONFIG ----------------
# --- Gemini Settings ---
TEST_MODE = False  # Set to True to use local dummy data and skip the API call.
MAX_PREVIEW_CHARS = 4000
GEMINI_MODEL = "gemini-2.5-flash-preview-09-2025" 

# --- n8n Settings (Update these with your real n8n webhook URL!) ---
# 🚨🚨 IMPORTANT: YOU MUST CHANGE THIS URL TO YOUR ACTUAL N8N WEBHOOK ADDRESS! 🚨🚨
N8N_WEBHOOK_URL = "http://localhost:5678/webhook/b7c126d1-1832-4430-a468-bf85a69bbd72" 
N8N_ACTIVE = True # Set to False if you haven't set up the N8N webhook yet.

# --- Job Title List (100+ items) ---
JOB_TITLES = [
    "Data Analyst", "Data Scientist", "Software Engineer", "Prompt Engineer",
    "Machine Learning Engineer", "DevOps Engineer", "Cloud Architect", 
    "Full Stack Developer", "Frontend Developer", "Backend Developer", 
    "Product Manager", "Project Manager", "UX/UI Designer", 
    "Business Analyst", "Financial Analyst", "Marketing Manager",
    "Sales Executive", "HR Manager", "Technical Writer", "Network Engineer",
    "Database Administrator", "Cyber Security Analyst", "IT Support Specialist",
    "Solutions Architect", "Research Scientist", "Biomedical Engineer",
    "Civil Engineer", "Mechanical Engineer", "Electrical Engineer",
    "Aerospace Engineer", "Chemical Engineer", "Industrial Engineer",
    "Operations Manager", "Supply Chain Analyst", "Logistics Coordinator",
    "Accountant", "Auditor", "Investment Banker", "Compliance Officer",
    "Recruiter", "Training Specialist", "Content Creator", "SEO Specialist",
    "Social Media Manager", "Copywriter", "Paralegal", "Attorney",
    "Physician Assistant", "Registered Nurse", "Physical Therapist",
    "Occupational Therapist", "Pharmacist", "Geologist", "Meteorologist",
    "Statistician", "Economist", "Actuary", "Quality Assurance Engineer",
    "Embedded Systems Engineer", "Mobile App Developer (iOS)", "Mobile App Developer (Android)",
    "Game Developer", "System Administrator", "Scrum Master", "Agile Coach",
    "Technical Consultant", "Data Engineer", "Bioinformatician", "Quant Developer",
    "Ethical Hacker", "VFX Artist", "Sound Engineer", "Chemist",
    "Physicist", "Mathematician", "Librarian", "Curator", 
    "Urban Planner", "Architect", "Landscape Architect", "Environmental Scientist",
    "Geospatial Analyst", "Petroleum Engineer", "Drilling Engineer", "Field Engineer",
    "Sales Engineer", "Customer Success Manager", "Technical Sales Representative",
    "Chief Technology Officer (CTO)", "Chief Financial Officer (CFO)", "Chief Operating Officer (COO)",
    "Warehouse Manager", "CNC Programmer", "Welder", "Electrician",
    "Plumber", "HVAC Technician", "Automotive Technician", "Flight Attendant",
    "Pilot", "Teacher (High School)", "Professor (University)", "Linguist",
    "Interpreter", "Translator", "Public Relations Specialist", "Event Manager"
]


# --- Set up the Streamlit Page Configuration ---
st.set_page_config(
    page_title="AI Resume Matcher", 
    page_icon="🤖", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------- Utility Functions ----------------

def fake_ai_analyze(resume_text, job_title):
    """Simple heuristic analysis for testing without real AI."""
    # Score variance based on job_title match
    score = 80 if "Data Analyst" in job_title else 65
    
    return {
        "skills": ["Python", "SQL", "Power BI", "Tableau", "Pandas"], 
        "experience_years": 0.0,
        "summary": "This is a detailed demo summary showing strong foundational data skills.",
        "ats_score": score,
        "education_summary": "Master’s in CS (Pursuing); B.Tech in CS (2025); Diploma in Engineering (2022).",
        "improvements": [
            f"Summary: Focus your summary on {job_title} keywords.",
            "Experience: Quantify project achievements using numbers.",
            "Skills: Expand on soft skills."
        ]
    }

def extract_text_from_pdf_file(file_obj):
    """Extracts text from a PDF using pdfplumber."""
    # ... (same as before)
    text = ""
    try:
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                ptext = page.extract_text()
                if ptext:
                    text += ptext + "\n"
    except Exception as e:
        st.error(f"Could not extract PDF text. It might be scanned (image-based). Error: {e}")
        return ""
    return text

def send_to_n8n(data):
    """Sends the analysis results to the configured n8n webhook."""
    if not N8N_ACTIVE:
        return
    
    st.info(f"📤 Attempting to send data to n8n webhook...")
    
    if "your-n8n-host" in N8N_WEBHOOK_URL:
        st.error("❌ Automation Failed: N8N_WEBHOOK_URL is still set to the placeholder 'your-n8n-host'. Please update it in the CONFIG section of the code.")
        return
        
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=data, timeout=10)
        response.raise_for_status()
        st.success(f"✅ Data sent to n8n successfully! Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Automation Failed: {e}")
        st.caption("Double-check that your n8n instance is running and the Webhook URL is correct.")

def call_gemini_api(resume_text, job_title):
    """Calls Gemini AI with structured JSON request and handles exponential backoff."""
    if TEST_MODE:
        return fake_ai_analyze(resume_text, job_title)
        
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("🚨 API Key not found. Falling back to Demo Output.")
        return fake_ai_analyze(resume_text, job_title)

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={api_key}"
    
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "skills": {"type": "ARRAY", "description": "A list of 5-10 technical and soft skills extracted.", "items": {"type": "STRING"}},
            "experience_years": {"type": "NUMBER", "description": "Total professional experience in years. Use 0 for entry-level."},
            "summary": {"type": "STRING", "description": "A concise, 1-2 sentence summary of the resume's focus."},
            "ats_score": {"type": "INTEGER", "description": "An ATS score from 0 to 100 based on keyword density, formatting, AND SPECIFICALLY how well the content matches the requirements for a '{job_title}' role."},
            "education_summary": {"type": "STRING", "description": "A comprehensive summary of all major academic achievements, including all degrees, diplomas, institutions, and completion years (e.g., 'Master's in CS (Pursuing); B.Tech in IT (2022); Diploma in CS (2019)')."}, 
            "improvements": {"type": "ARRAY", "description": "A list of 3-5 actionable suggestions focused on how to improve the resume for the '{job_title}' role.", "items": {"type": "STRING"}}
        },
        "required": ["skills", "experience_years", "summary", "ats_score", "improvements", "education_summary"] 
    }

    prompt = f"""
    You are an expert Applicant Tracking System (ATS) resume analyzer. Your task is to analyze the provided resume text and determine its fitness for the role of a '{job_title}'.

    1. Calculate ATS Score: Generate an ATS score (0-100) based on keyword density, formatting, and the relevance of the candidate's experience and skills specifically to the '{job_title}' role requirements.
    2. Provide Focused Improvements: Provide actionable suggestions focused on how the candidate can improve their resume to better match the '{job_title}' role. Crucially, prefix each suggestion with the specific resume section it relates to (e.g., 'Summary:', 'Experience:', 'Skills:', 'Education:').
    3. Generate Structured JSON: Output the final analysis in the defined JSON format.

    Resume text to analyze:
    ---
    {resume_text}
    ---
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }
    }

    # Exponential Backoff
    max_retries = 3
    base_delay = 1 

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers={"Content-Type": "application/json"}, json=payload)
            response.raise_for_status() 
            result = response.json()

            candidate = result.get("candidates", [])
            if candidate and candidate[0].get("content"):
                json_text = candidate[0]["content"]["parts"][0]["text"]
                return json.loads(json_text)
            
            raise Exception("API returned an empty or blocked candidate response.")

        except requests.exceptions.RequestException as req_err:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                st.error(f"🚨 Final API request failed: {req_err}")
                break
        except Exception as e:
            st.error(f"🚨 Error processing AI response: {e}")
            break 

    st.warning("⚠ Gemini API failed. Falling back to Demo Output.")
    return fake_ai_analyze(resume_text, job_title)

# ---------------- UI Visualization Functions ----------------

def animated_gauge_chart(score):
    """Generates an HTML component for an animated gauge chart."""
    
    # Calculate colors based on score
    if score >= 80:
        color = "#10b981"  # Green
    elif score >= 50:
        color = "#f59e0b"  # Yellow/Orange
    else:
        color = "#ef4444"  # Red

    # Map score (0-100) to an angle (45 deg to 315 deg)
    # 45 is the start, 315 is the end. Total range is 270 degrees.
    angle = 45 + (score / 100) * 270
    
    # SVG and CSS for the Gauge Chart
    # Increased size (250x125) and removed the central white circle.
    html_code = f"""
    <style>
        @import url('https://fonts2.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        .gauge-container {{
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            font-family: 'Inter', sans-serif;
        }}
        .gauge-svg-wrapper {{
            position: relative;
            width: 250px; /* Increased size significantly for better visibility */
            height: 150px; /* Sufficient height to prevent top clipping */
            /* overflow: hidden REMOVED to prevent clipping */
        }}
        .gauge-bg {{
            fill: none;
            stroke: #e5e7eb;
            stroke-width: 25; 
        }}
        .gauge-arc {{
            fill: none;
            stroke: {color};
            stroke-width: 20; 
            stroke-linecap: round;
            transform: rotate(180deg);
            transform-origin: 50% 100%;
            stroke-dasharray: 706.86;
            stroke-dashoffset: 706.86;
            transition: stroke-dashoffset 2s ease-out; 
        }}
        .gauge-label {{
            position: absolute;
            top: 50%; /* Center vertically within the wrapper */
            transform: translateY(-30%); /* Fine-tune position */
            text-align: center;
            width: 100%;
            font-size: 3.5rem; /* Increased font size for clarity */
            font-weight: 700;
            color: #374151;
        }}
        .gauge-title {{
             font-size: 1.3rem; 
             color: #6b7280;
             margin-top: 10px; /* Adjusted margin */
        }}       
    </style>
    <div class="gauge-container">
        <div class="gauge-svg-wrapper">
            <svg viewBox="0 0 250 125" preserveAspectRatio="none">
                <!-- Background arc uses r=112.5 (from 12.5 to 237.5) and center (125, 115) to maintain arc size -->
                <path class="gauge-bg" d="M12.5 115 A112.5 112.5 0 0 1 237.5 115" /> 
                <!-- Animated arc -->
                <path id="gaugeArc" class="gauge-arc" d="M12.5 115 A112.5 112.5 0 0 1 237.5 115" />
                <!-- Center pivot point removed -->
            </svg>
            <div id="gaugeLabel" class="gauge-label">0%</div>
        </div>
        <div class="gauge-title">ATS Match Score</div>
    </div>

    <script>
        const score = {score};
        const angle = {angle};
        const arc = document.getElementById('gaugeArc');
        const label = document.getElementById('gaugeLabel');
        // Circumference for a 3/4 circle with r=112.5 is 2 * PI * 112.5 * 0.75 = 530.14. 
        // Re-calibrating stroke-dasharray based on the actual SVG path length, which is approx 706.86 based on viewBox changes.
        const circumference = 706.86; 
        
        // Calculate offset for the final score (0 = 100%)
        const offset = circumference * (1 - (score / 100));

        // Start animation after a short delay to ensure rendering
        setTimeout(() => {{
            arc.style.strokeDashoffset = offset;
        }}, 50);

        // Animate the label text from 0 to final score
        let currentScore = 0;
        const duration = 2000; // 2 seconds
        const startTime = performance.now();

        function animate(currentTime) {{
            const elapsedTime = currentTime - startTime;
            const progress = Math.min(elapsedTime / duration, 1);
            
            currentScore = Math.round(progress * score);
            label.textContent = currentScore + '%';
            
            if (progress < 1) {{
                requestAnimationFrame(animate);
            }}
        }}

        requestAnimationFrame(animate);

    </script>
    """
    st.components.v1.html(html_code, height=250)

# ---------------- UI Layout (Enhanced) ----------------

# Header and Introduction
st.markdown(
    """
    <div style='background-color: #1f77b4; padding: 20px; border-radius: 10px;'>
        <h1 style='color: white; text-align: center; margin-bottom: 0px;'>
            🤖 AI Resume Matcher & Analyzer
        </h1>
        <p style='color: #c7e9ff; text-align: center; font-size: 1.1em;'>
            Upload your PDF and match it against a target job for a calculated ATS score and improvements.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

with st.expander("❓ How It Works"):
    st.markdown("""
    1. Target Job: Select the job title you are applying for. The AI will calculate the score based on how well your resume matches the requirements of that specific role (e.g., matching 'Software Engineer' keywords).
    2. Upload: Upload your PDF resume.
    3. Analysis: The Gemini model acts as an ATS, calculating your match score and providing targeted advice.
    4. Animated Gauge: The match score is displayed on an animated gauge chart for a clear, real-time result.
    """)

st.markdown("---")

# --- INPUT SECTION ---
st.subheader("1. Target Job & Resume Upload")
col_job, col_file = st.columns(2)

with col_job:
    # Dropdown with search functionality (autocomplete) for 100+ job titles
    job_title = st.selectbox(
        "Select Your Target Job Role:",
        options=JOB_TITLES,
        index=JOB_TITLES.index("Data Analyst") if "Data Analyst" in JOB_TITLES else 0
    )
    
with col_file:
    uploaded_file = st.file_uploader(
        "Upload Your Resume (PDF):", 
        type=["pdf"], 
        label_visibility="visible"
    )

st.markdown("---")

# --- ANALYSIS TRIGGER ---

if uploaded_file and job_title:
    
    bytes_data = uploaded_file.read()
    file_like = BytesIO(bytes_data)

    st.success(f"File {uploaded_file.name} uploaded successfully. Matching against: {job_title}.")
    
    # Text Extraction
    raw_text = extract_text_from_pdf_file(file_like)
    
    # Analysis Button
    if st.button(f"🚀 ANALYZE MATCH FOR {job_title.upper()}", type="primary", use_container_width=True):
        if not raw_text:
            st.error("Cannot analyze an empty resume.")
        else:
            with st.spinner(f"🧠 Calculating ATS match score for {job_title}..."):
                analysis = call_gemini_api(raw_text, job_title)

            st.session_state['analysis'] = analysis
            st.session_state['job_title'] = job_title
            
            st.markdown("## 🎯 Match Analysis Complete!")
            
            # --- 1. Display Visual Metrics ---
            
            score_col, exp_col, skill_col = st.columns([1.5, 1, 1])

            with score_col:
                st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
                animated_gauge_chart(analysis.get("ats_score", 0))

            
            with exp_col:
                st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
                st.metric(
                    label="⏳ Experience (Years)", 
                    value=analysis.get("experience_years", "N/A"),
                    help="Total professional experience interpreted from dates in the document."
                )
                
            with skill_col:
                st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
                st.metric(
                    label="💡 Skills Identified", 
                    value=len(analysis.get("skills", [])),
                    help="The total number of unique technical and soft skills the AI recognized."
                )

            st.markdown("---")

            # --- 2. Summary and Skills ---

            st.subheader("📝 Key Summary")
            st.info(f"{analysis.get('summary')}", icon="✨")

            st.subheader("🛠 Skills Found")
            skills_list = analysis.get("skills", [])
            st.markdown(f'<div style="background-color: #e0f7fa; padding: 10px; border-left: 5px solid #00bcd4; border-radius: 5px;">{", ".join(skills_list) or "No major skills detected."}</div>', unsafe_allow_html=True)
            
            st.markdown("---")
            
            # --- EDUCATION SECTION (Formatted as a list) ---
            st.subheader("🎓 Education Summary")
            education_text = analysis.get("education_summary", "Not found or unclear.")
            
            if education_text and education_text != "Not found or unclear.":
                education_items = education_text.split(';')
                formatted_education = ""
                for item in education_items:
                    formatted_education += f"- {item.strip()}\n"
                st.info(formatted_education, icon="📚")
            else:
                st.info(f"{education_text}", icon="📚")

            st.markdown("---")

            # --- 3. Targeted Improvements (NEW GROUPED DISPLAY) ---
            st.subheader(f"📌 Targeted Improvements for {job_title}")
            
            improvement_list = analysis.get("improvements", [])
            
            # Grouping logic
            improvement_groups = {
                "Summary": [],
                "Skills": [],
                "Experience": [],
                "Education": [],
                "General": []
            }

            for item in improvement_list:
                # Try to extract the section prefix (e.g., "Experience:")
                parts = item.split(':', 1)
                if len(parts) == 2:
                    section = parts[0].strip().title()
                    content = parts[1].strip()
                else:
                    section = "General"
                    content = item.strip()
                
                # Use standard groups or fall back to General
                if section in improvement_groups:
                    improvement_groups[section].append(content)
                else:
                    improvement_groups["General"].append(content)

            # Displaying the grouped improvements
            for section, items in improvement_groups.items():
                if items:
                    # Use a distinct styling for the section headers and feedback blocks
                    st.markdown(f"#### ✍ {section} Enhancements")
                    
                    # Format the list content
                    list_markdown = ""
                    for item in items:
                        list_markdown += f"- {item}\n"
                    
                    # Use a distinct visual element for the categorized feedback
                    # Yellow background (#fef3c7) with orange border (#fbbf24) for Warning/Improvement
                    st.markdown(f'<div style="background-color: #fef3c7; border-left: 5px solid #fbbf24; padding: 10px; margin-bottom: 15px; border-radius: 5px;">{list_markdown}</div>', unsafe_allow_html=True)

            st.markdown("---")
            
            # 5. Send data to n8n webhook (The actual automation step)
            n8n_payload = {
                "filename": uploaded_file.name,
                "job_title": job_title,
                "extracted_text": raw_text,
                "analysis_results": analysis
            }
            send_to_n8n(n8n_payload)
            

else:
    st.info("⬆ Please select your target job and upload a resume PDF to begin the analysis.", icon="⬆")

# Display the analysis results persistently if they are in the session state
if 'analysis' in st.session_state:
    analysis = st.session_state['analysis']
    job_title = st.session_state['job_title']
    
    # This block is required to prevent the UI from clearing when the user changes the job title/uploads a file.
    if st.session_state.get('last_run_success', False):
        pass
