import streamlit as st
import subprocess
import sys
import os
import time
from pathlib import Path

# --- Configuration ---
BASE_DIR = Path(__file__).parent
INVOICES_DIR = BASE_DIR / "data" / "invoices"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
EXTRACTED_CONTENT_FILE = OUTPUTS_DIR / "extracted_content.txt"
FINAL_EXCEL_FILE = OUTPUTS_DIR / "invoices_data.xlsx"

# The sequence of agents to run for the pipeline
PIPELINE_AGENTS = {
    "ingestion_agent.py": "Extracting text and QR codes from all PDFs.",
    "validation_agent.py": "Validating data for all extracted invoices.",
    "logger_agent.py": "Consolidating all invoice data into a structured format.",
    "mapper_agent.py": "Mapping line items from all invoices to master data.",
    "gst_fetcher_agent.py": "Fetching GST rates for all invoices.",
    "reviewer_agent.py": "Performing final review and generating the consolidated report."
}

# --- Helper Functions ---

def setup_directories():
    """Ensure all necessary directories exist."""
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

def clear_previous_run_data():
    """Deletes old output and invoice files to ensure a clean batch run."""
    # Clear output files from previous runs
    if EXTRACTED_CONTENT_FILE.exists():
        EXTRACTED_CONTENT_FILE.unlink()
    if FINAL_EXCEL_FILE.exists():
        FINAL_EXCEL_FILE.unlink()
    # Clear any leftover PDFs from the invoices directory
    for pdf_file in INVOICES_DIR.glob("*.pdf"):
        pdf_file.unlink()

def run_agent(agent_name: str):
    """
    Runs a specific agent script as a subprocess and yields its output in real-time.
    """
    agent_path = BASE_DIR / "agents" / agent_name
    if not agent_path.exists():
        st.error(f"Error: Agent script not found at {agent_path}")
        return

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    process = subprocess.Popen(
        [sys.executable, str(agent_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        env=env
    )

    for line_bytes in iter(process.stdout.readline, b''):
        yield line_bytes.decode('utf-8', errors='ignore')
    
    process.stdout.close()
    return_code = process.wait()
    
    if return_code != 0:
        st.error(f"Agent '{agent_name}' failed with return code {return_code}. See logs for details.")
        st.stop()

# --- Streamlit UI ---

st.set_page_config(page_title="Invoice Processing Pipeline", layout="wide")

# --- Sidebar for Controls ---
with st.sidebar:
    st.header("Invoice Processor")
    st.markdown("Upload one or more PDF invoices to begin the automated batch processing pipeline.")
    
    # MODIFIED: Allow multiple file uploads
    uploaded_files = st.file_uploader(
        "Upload Invoice PDFs",
        type="pdf",
        accept_multiple_files=True
    )
    
    # MODIFIED: Button is disabled if the list of uploaded files is empty
    process_button = st.button("Process Invoices", type="primary", use_container_width=True, disabled=(not uploaded_files))

# --- Main Content Area ---
st.title("Batch Invoice Processing Dashboard")
st.markdown("---")

if not uploaded_files:
    st.info("Please upload one or more PDF files using the sidebar to begin processing.")

if process_button and uploaded_files:
    # 1. Setup and File Handling for multiple files
    setup_directories()
    clear_previous_run_data()
    
    st.subheader("Uploaded Files")
    file_names = []
    for uploaded_file in uploaded_files:
        pdf_path = INVOICES_DIR / uploaded_file.name
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_names.append(uploaded_file.name)
    
    # Display the list of files to be processed
    st.success(f"{len(file_names)} file(s) are ready for processing:")
    st.code("\n".join(file_names))
    time.sleep(1)

    # 2. Progress Bar and Status
    st.header("Processing Status")
    total_agents = len(PIPELINE_AGENTS)
    progress_bar = st.progress(0)
    status_text = st.empty()

    # 3. Execute Pipeline
    st.subheader("Agent Logs")
    
    for i, (agent, description) in enumerate(PIPELINE_AGENTS.items()):
        status_text.info(f"*Running:* {agent} ({description})")
        
        with st.expander(f"Logs for {agent}"):
            with st.spinner(f"Executing {agent}..."):
                for line in run_agent(agent):
                    st.text(line.strip())
        
        progress_value = (i + 1) / total_agents
        progress_bar.progress(progress_value)
    
    status_text.success("Pipeline completed successfully for all invoices.")

    st.markdown("---")
    st.header("Results")

    # 4. Provide Download Link for the consolidated report
    if FINAL_EXCEL_FILE.exists():
        st.subheader("Download Consolidated Report")
        with open(FINAL_EXCEL_FILE, "rb") as f:
            st.download_button(
                label="Download Processed Data (invoices_data.xlsx)",
                data=f,
                file_name="invoices_data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.error("Processing finished, but the final Excel report was not generated. Please review the agent logs for errors.")