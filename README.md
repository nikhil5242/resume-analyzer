# 🤖 AI Resume Intelligence & Automation Pipeline

## 📌 Project Overview
An end-to-end **AI-powered resume analysis and recruitment automation system** that evaluates resumes using **Google Gemini 2.0**, calculates an **ATS match score**, and automatically notifies HR for high-potential candidates using an **n8n-based workflow**.

This project goes beyond resume parsing—it functions as a **self-operating recruitment assistant**, reducing manual screening and accelerating hiring decisions.

---

## ⚙️ System Architecture & Workflow
The system is designed as a **real-world automation pipeline**, integrating AI, web applications, and low-code workflow orchestration.

### 🔁 How the Pipeline Works
1. **Frontend (Streamlit App)**  
   Users upload resumes (PDF) through a Streamlit-based web interface.

2. **AI Intelligence (Gemini 2.0)**  
   Google **Gemini 2.0 API** parses unstructured resume text and evaluates it against job requirements to generate an **ATS Match Score**.

3. **Decision Logic**  
   If the ATS score is **greater than 80%**, the system triggers an automation event.

4. **Automation Trigger (Webhook)**  
   The Streamlit app sends candidate data to an **n8n Webhook** endpoint.

5. **Workflow Orchestration (n8n)**  
   - **IF Node:** Validates ATS score condition  
   - **Email Node (SMTP):** Automatically sends an email alert to HR with candidate details

6. **Networking & Tunneling**  
   **ngrok** is used to expose the local n8n webhook, enabling real-time external triggers from the Streamlit app.

---

## ✨ Key Features
- AI-powered resume parsing using **Google Gemini 2.0**
- Dynamic **ATS score calculation** based on job fit
- Conditional automation using **n8n IF nodes**
- Automatic HR email notifications for high-scoring candidates
- End-to-end workflow with **zero manual intervention**
- Real-time processing via webhook integration

---

## 🛠️ Tech Stack
| Layer | Technology |
|-----|-----------|
| LLM | **Google Gemini 2.0 API** |
| Frontend | Streamlit (Python) |
| Automation | n8n (Low-code Workflow Engine) |
| Networking | ngrok (Webhook tunneling) |
| Backend | Python (Pandas, Requests, Dotenv) |
| Integration | REST APIs & Webhooks |
| Notifications | SMTP Email Service |

---

## 📊 Sample Output
- Parsed resume data in structured JSON format  
- ATS Match Score (0–100%)  
- Automated HR email notification for candidates scoring **>80%**  
- Resume evaluation results displayed instantly in the Streamlit UI  



