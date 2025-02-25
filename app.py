# app.py (Final Updated Version)
import os
import io
import base64
import traceback
from tenacity import retry, stop_after_attempt, wait_exponential
import PyPDF2
from rapidfuzz import fuzz
import streamlit as st
from google.genai import types
import prompts
from utils import summarize_common

os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"]="15"
# ==============================================================
# UI Configuration & Branding
# ==============================================================
st.set_page_config(
    page_title="SummarizerIQ",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Modern UI
st.markdown(f"""
<style>
            

            
/* Center the logo container */
.logo-container {{
  display: flex;
  justify-content: center;
  margin: 1rem 0 2rem 0;
}}
.logo-container img {{
  width: 80px;
  height: auto;
}}

/* Standard paragraph styling */
p {{
  color: #000;
}}

/* Main Container with white background */
.main {{
  background-color: #ffffff;
  padding: 2rem 1rem;
}}

/* Logo Header updated to a clean white background */
.logo-header {{
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}}

/* Sidebar Styling remains white */
[data-testid="stSidebar"] {{
  background: #ffffff !important;
  border-right: 1px solid #e2e8f0;
}}

/* Button Styling using green color */
.stButton>button {{
  background-color: #28a745 !important; /* Modern green */
  color: #ffffff !important;
  border: none;
  border-radius: 8px !important;
  padding: 0.75rem 1.5rem !important;
  transition: background-color 0.2s ease, transform 0.2s ease;
}}
.stButton>button:hover {{
  background-color: #218838 !important; /* Darker green on hover */
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(33, 136, 56, 0.2);
}}

/* File Uploader */
[data-testid="stFileUploader"] {{
  border: 2px dashed #cbd5e1 !important;
  border-radius: 12px !important;
  padding: 2rem !important;
}}

/* Chat Messages */
.chat-message {{
  padding: 1.25rem;
  border-radius: 12px;
  margin-bottom: 1rem;
  background: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  border: 1px solid #e2e8f0;
}}
</style>

""", unsafe_allow_html=True)

# Logo and Header
with st.container():
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        st.image("assets/logo.png", width=90)  
    with col2:
        st.title("SummarizeIQ")
        

# Initialize session state
if "pdf_parts" not in st.session_state:
    st.session_state.pdf_parts = []
if "summary" not in st.session_state:
    st.session_state.summary = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "page_refs" not in st.session_state:
    st.session_state.page_refs = {}
if "questions" not in st.session_state:
    st.session_state.questions = []

# ==============================================================
# Helper Functions
# ==============================================================
def find_matching_page(response_text):
    """Fuzzy match response text with PDF content"""
    best_match = ("N/A", 0)
    for page_num, content in st.session_state.page_refs.items():
        score = fuzz.partial_ratio(response_text.lower(), content.lower())
        if score > best_match[1]:
            best_match = (page_num.split("_")[1], score)
    return best_match[0] if best_match[1] > 75 else "N/A"

# ==============================================================
# Modern Sidebar Design
# ==============================================================
with st.sidebar:
    st.markdown("### ⚙️ Analysis Settings")
    analysis_mode = st.selectbox(
        "**Analysis Depth**",
        ["Quick Scan", "Detailed Analysis", "Deep Dive"],
        help="Select the depth of document analysis"
    )
    
    response_style = st.radio(
        "**Response Style**",
        ["Casual", "Professional", "Academic"],
        horizontal=True,
        help="Choose the tone for responses"
    )

# ==============================================================
# Modern Document Upload Section
# ==============================================================
with st.expander("📤 Upload Document", expanded=True):
    doc_col, upload_col = st.columns([0.4, 0.6])
    with doc_col:
        doc_type = st.selectbox(
            "Document Type",
            ("Research paper", "Literature Review", "Report"),
            index=0,
            label_visibility="collapsed"
        )
    
    with upload_col:
        uploaded_file = st.file_uploader(
            "Choose PDF file",
            type=["pdf"],
            label_visibility="collapsed"
        )
    
    process_btn = st.button("Analyze Document", type="primary", use_container_width=True)

# ==============================================================
# Processing Pipeline
# ==============================================================
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def process_document(file, doc_type, analysis_mode):
    """Robust document processing with retries"""
    with st.status(f"🔍 Analyzing {doc_type}...", expanded=True) as status:
        try:
            content = file.read()
            base64_pdf = base64.b64encode(content)
            
            # Extract page references
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            st.session_state.page_refs = {f"page_{i+1}": page.extract_text()[:1000] 
                                        for i, page in enumerate(pdf_reader.pages)}
            
            st.write("Extracting document structure...")
            document_part = types.Part.from_bytes(
                data=base64.b64decode(base64_pdf),
                mime_type="application/pdf"
            )
            
            st.write("Identifying key sections...")
            prompt_map = {
                "Research paper": prompts.research_paper_prompt,
                "Literature Review": prompts.literature_review_prompt,
                "Report": prompts.report_prompt
            }
            
            st.write("Generating insights...")
            summary = summarize_common(
                system_prompt=prompts.system_prompt.format(
                    document_name=doc_type,
                    style=response_style,
                    depth=analysis_mode
                ),
                parts=[types.Part.from_text(text=prompt_map[doc_type]), document_part],
                analysis_mode=analysis_mode
            )
            
            status.update(label="Analysis Complete! 🎉", state="complete")
            return document_part, summary
            
        except Exception as e:
            status.update(label="Analysis Failed ❌", state="error")
            raise e

if process_btn and uploaded_file:
    if uploaded_file.size > 15 * 1024 * 1024:
        st.error("⚠️ File size exceeds 15MB limit")
    else:
        try:
            document_part, summary = process_document(uploaded_file, doc_type, analysis_mode)
            st.session_state.pdf_parts = [document_part]
            st.session_state.summary = summary
            st.session_state.messages = []
            st.rerun()
            
        except Exception as e:
            st.error(f"Processing failed: {str(e)}")
            traceback.print_exc()

# ==============================================================
# Modern Results Display
# ==============================================================
if st.session_state.summary:
    with st.expander("📑 Executive Summary", expanded=True):
        st.markdown(f"""
            <div style='padding: 1.5rem; background: #ffffff; border-radius: 12px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);'>
                <h3 style='color: #6366f1; margin-bottom: 1rem;'>{doc_type} Summary</h3>
                <div style='line-height: 1.6; color: #475569;'>{st.session_state.summary}</div>
            </div>
        """, unsafe_allow_html=True)
        
        dl_col, q_col = st.columns([0.3, 0.7])
        with dl_col:
            st.download_button(
                "📥 Download Summary",
                st.session_state.summary,
                file_name=f"{doc_type}_summary.md",
                use_container_width=True
            )
        with q_col:
            if st.button("❓ Generate Discussion Points", use_container_width=True):
                try:
                    questions = summarize_common(
                        system_prompt=prompts.question_prompt,
                        parts=[types.Part.from_text(text=st.session_state.summary)]
                    )
                    # Clean and validate questions
                    st.session_state.questions = [
                        q.strip() for q in questions.split("\n") 
                        if q.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "-", "*"))
                    ]
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to generate questions: {str(e)}")
                    traceback.print_exc()

# ==============================================================
# Modern Chat Interface
# ==============================================================
st.divider()

if st.session_state.pdf_parts:
    st.markdown("### 💬 Document Dialogue")
    
    # Clear conversation button
    if st.session_state.messages:
        if st.button("🧹 Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.success("Conversation history cleared!")
            st.rerun()

    # Chat messages
    for msg in st.session_state.messages:
        with st.container():
            st.markdown(f"""
                <div class="chat-message" style='background: { "#f8fafc" if msg["role"] == "user" else "white" };'>
                    <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                        <span style='font-size: 1.2rem; margin-right: 0.75rem;'>
                            {"👤" if msg["role"] == "user" else "🤖"}
                        </span>
                        <strong style='color: #6366f1;'>{"You" if msg["role"] == "user" else "DocIQ"}</strong>
                    </div>
                    <div style='color: #475569; line-height: 1.6;'>{msg["content"]}</div>
                    {"<div style='font-size: 0.85rem; color: #64748b; margin-top: 0.75rem;'>📌 " + msg["sources"] + "</div>" if "sources" in msg else ""}
                </div>
            """, unsafe_allow_html=True)

    # Display questions
    if st.session_state.questions:
        with st.expander("💡 Suggested Discussion Points"):
            for idx, q in enumerate(st.session_state.questions):
                if q and len(q) > 10:
                    if st.button(q, key=f"question_{idx}"):
                        st.session_state.messages.append({"role": "user", "content": q})

    # Chat input
    if prompt := st.chat_input("Ask about the document..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        try:
            response = summarize_common(
                system_prompt=prompts.chat_prompt.format(style=response_style),
                parts=[types.Part.from_text(text=prompt)] + st.session_state.pdf_parts
            )
            
            matched_page = find_matching_page(response)
            source = f"Page {matched_page}" if matched_page != "N/A" else "Document Context"
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "sources": source
            })
            st.rerun()
            
        except Exception as e:
            st.error(f"Response generation failed: {str(e)}")