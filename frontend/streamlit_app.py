"""
Streamlit frontend for the QA Agent.
"""
import streamlit as st
import requests
import json
from typing import List, Dict, Optional

# Page configuration
st.set_page_config(
    page_title="Autonomous QA Agent",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if 'test_cases' not in st.session_state:
    st.session_state.test_cases = []
if 'selected_test_case' not in st.session_state:
    st.session_state.selected_test_case = None

# Configuration
st.sidebar.title("⚙️ Configuration")
backend_url = st.sidebar.text_input(
    "Backend API URL",
    value="http://localhost:8000/api",
    help="Base URL for the FastAPI backend"
)

# Main title
st.title("🤖 Autonomous QA Agent")
st.markdown("**Test Case and Script Generation Tool**")
st.markdown("---")

# Helper function to make API requests
def make_api_request(endpoint: str, method: str = "POST", files: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Optional[Dict]:
    """
    Make API request to backend.
    
    Args:
        endpoint: API endpoint (without base URL)
        method: HTTP method
        files: Files to upload (for multipart/form-data)
        json_data: JSON data to send
        
    Returns:
        Response JSON or None if error
    """
    url = f"{backend_url.rstrip('/')}/{endpoint.lstrip('/')}"
    
    try:
        if method == "POST":
            if files:
                response = requests.post(url, files=files, timeout=60)
            elif json_data:
                response = requests.post(url, json=json_data, timeout=60)
            else:
                response = requests.post(url, timeout=60)
        else:
            response = requests.get(url, timeout=60)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Cannot connect to backend at {url}. Make sure the FastAPI server is running.")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ Request timed out. The backend may be processing a large request.")
        return None
    except requests.exceptions.HTTPError as e:
        error_detail = "Unknown error"
        try:
            error_response = response.json()
            error_detail = error_response.get("detail", str(e))
        except:
            error_detail = str(e)
        st.error(f"❌ Error: {error_detail}")
        return None
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        return None

# Section 1: Document Upload
st.header("📄 Document Upload")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Support Documents")
    st.markdown("Upload markdown, text, JSON, or PDF files")
    support_docs = st.file_uploader(
        "Select support documents",
        type=["md", "txt", "json", "pdf"],
        accept_multiple_files=True,
        key="support_docs"
    )
    
    if support_docs:
        st.info(f"📎 {len(support_docs)} file(s) selected")
        for doc in support_docs:
            st.text(f"  • {doc.name}")

with col2:
    st.subheader("Checkout HTML")
    st.markdown("Upload checkout.html file")
    checkout_html = st.file_uploader(
        "Select checkout.html",
        type=["html", "htm"],
        accept_multiple_files=False,
        key="checkout_html"
    )
    
    if checkout_html:
        st.info(f"📎 {checkout_html.name} selected")

# Upload button
if st.button("📤 Upload Files", type="primary", use_container_width=True):
    if not support_docs and not checkout_html:
        st.warning("⚠️ Please select at least one file to upload.")
    else:
        upload_results = []
        
        # Upload support documents
        if support_docs:
            with st.spinner("Uploading support documents..."):
                # Prepare files for multipart upload
                # FastAPI expects multiple files with the same field name "files"
                files_list = []
                for doc in support_docs:
                    doc.seek(0)  # Reset file pointer
                    files_list.append(("files", (doc.name, doc.read(), doc.type or "application/octet-stream")))
                
                # Make request with all files
                response = make_api_request(
                    "upload-docs",
                    files=files_list
                )
                
                if response:
                    upload_results.append(("Support Documents", response))
        
        # Upload checkout.html
        if checkout_html:
            with st.spinner("Uploading checkout.html..."):
                checkout_html.seek(0)  # Reset file pointer
                files_dict = {
                    "file": (checkout_html.name, checkout_html.read(), checkout_html.type or "text/html")
                }
                
                response = make_api_request(
                    "upload-html",
                    files=files_dict
                )
                
                if response:
                    upload_results.append(("Checkout HTML", response))
        
        # Display results
        if upload_results:
            st.success("✅ Files uploaded successfully!")
            for title, result in upload_results:
                with st.expander(f"📋 {title} Upload Details"):
                    st.json(result)

st.markdown("---")

# Section 2: Knowledge Base
st.header("🧠 Knowledge Base")

if st.button("🔨 Build Knowledge Base", type="primary", use_container_width=True):
    with st.spinner("Building knowledge base from uploaded documents..."):
        response = make_api_request("build-knowledge-base")
        
        if response:
            st.success("✅ Knowledge base built successfully!")
            
            summary = response.get("summary", {})
            
            # Display summary in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Documents", summary.get("total_documents", 0))
            
            with col2:
                st.metric("Total Chunks", summary.get("total_chunks", 0))
            
            with col3:
                errors_count = len(summary.get("errors", []))
                if errors_count > 0:
                    st.metric("Errors", errors_count, delta=None, delta_color="inverse")
                else:
                    st.metric("Errors", 0)
            
            # Detailed summary
            with st.expander("📊 Detailed Summary"):
                st.json(summary)
                
                # Show support docs
                if summary.get("support_docs"):
                    st.subheader("Support Documents")
                    for doc in summary["support_docs"]:
                        st.text(f"  • {doc['filename']} ({doc['chunks']} chunks)")
                
                # Show HTML files
                if summary.get("html_files"):
                    st.subheader("HTML Files")
                    for html_file in summary["html_files"]:
                        st.text(f"  • {html_file['filename']} ({html_file['chunks']} chunks)")
                
                # Show errors if any
                if summary.get("errors"):
                    st.subheader("⚠️ Errors")
                    for error in summary["errors"]:
                        st.error(f"  • {error['filename']}: {error['error']}")

st.markdown("---")

# Section 3: Test Case Generation
st.header("📝 Test Case Generation")

# Text area for query
default_query = "Generate all positive and negative test cases for the discount code feature."
test_case_query = st.text_area(
    "Test Case Request",
    value=default_query,
    height=100,
    help="Describe what test cases you want to generate. Be specific about features and test types."
)

# Generate button
if st.button("✨ Generate Test Cases", type="primary", use_container_width=True):
    if not test_case_query or not test_case_query.strip():
        st.warning("⚠️ Please enter a test case request.")
    else:
        with st.spinner("Generating test cases using RAG..."):
            response = make_api_request(
                "generate-test-cases",
                json_data={"query": test_case_query}
            )
            
            if response:
                test_cases = response.get("test_cases", [])
                
                if test_cases:
                    st.success(f"✅ Generated {len(test_cases)} test case(s)!")
                    
                    # Store in session state
                    st.session_state.test_cases = test_cases
                    
                    # Display test cases in a table
                    st.subheader("📋 Generated Test Cases")
                    
                    # Create a selectbox for test case selection
                    test_case_options = [
                        f"{tc['test_id']}: {tc['test_scenario']}" 
                        for tc in test_cases
                    ]
                    
                    selected_index = st.selectbox(
                        "Select a test case to view details or generate Selenium script:",
                        range(len(test_case_options)),
                        format_func=lambda x: test_case_options[x],
                        key="test_case_selector"
                    )
                    
                    if selected_index is not None:
                        st.session_state.selected_test_case = test_cases[selected_index]
                    
                    # Display all test cases in an expandable table
                    with st.expander("📊 View All Test Cases"):
                        # Convert to DataFrame for better display
                        import pandas as pd
                        
                        df_data = []
                        for tc in test_cases:
                            df_data.append({
                                "Test ID": tc.get("test_id", ""),
                                "Feature": tc.get("feature", ""),
                                "Scenario": tc.get("test_scenario", ""),
                                "Type": tc.get("test_type", ""),
                                "Steps": len(tc.get("steps", [])),
                                "Source Docs": ", ".join(tc.get("grounded_in", []))
                            })
                        
                        df = pd.DataFrame(df_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.warning("⚠️ No test cases were generated. Try refining your query.")
            else:
                st.error("❌ Failed to generate test cases. Check backend connection and logs.")

# Display selected test case details
if st.session_state.selected_test_case:
    st.markdown("---")
    st.subheader("🔍 Selected Test Case Details")
    
    tc = st.session_state.selected_test_case
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Test ID:** `{tc.get('test_id', 'N/A')}`")
        st.markdown(f"**Feature:** {tc.get('feature', 'N/A')}")
        st.markdown(f"**Test Type:** {tc.get('test_type', 'N/A')}")
        st.markdown(f"**Preconditions:** {tc.get('preconditions', 'None')}")
    
    with col2:
        st.markdown(f"**Scenario:** {tc.get('test_scenario', 'N/A')}")
        st.markdown(f"**Expected Result:** {tc.get('expected_result', 'N/A')}")
        if tc.get('grounded_in'):
            st.markdown(f"**Source Documents:** {', '.join(tc['grounded_in'])}")
    
    st.markdown("**Test Steps:**")
    steps = tc.get('steps', [])
    if steps:
        for i, step in enumerate(steps, 1):
            st.markdown(f"{i}. {step}")
    else:
        st.text("No steps defined")

st.markdown("---")

# Section 4: Selenium Script Generation
st.header("🐍 Selenium Script Generation")

if not st.session_state.selected_test_case:
    st.info("ℹ️ Please generate and select a test case first to generate a Selenium script.")
else:
    st.info(f"📋 Selected Test Case: **{st.session_state.selected_test_case.get('test_id', 'N/A')}** - {st.session_state.selected_test_case.get('test_scenario', 'N/A')}")
    
    if st.button("🚀 Generate Selenium Script", type="primary", use_container_width=True):
        with st.spinner("Generating Selenium script..."):
            response = make_api_request(
                "generate-selenium-script",
                json_data=st.session_state.selected_test_case
            )
            
            if response:
                script = response.get("script", "")
                
                if script:
                    st.success("✅ Selenium script generated successfully!")
                    
                    # Display script in code block
                    st.subheader("📜 Generated Python Script")
                    st.code(script, language="python")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Script",
                        data=script,
                        file_name=f"test_{st.session_state.selected_test_case.get('test_id', 'test')}.py",
                        mime="text/x-python"
                    )
                else:
                    st.warning("⚠️ No script was generated. Check backend logs.")
            else:
                st.error("❌ Failed to generate Selenium script. Check backend connection and logs.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <small>Autonomous QA Agent - Test Case and Script Generation Tool</small>
    </div>
    """,
    unsafe_allow_html=True
)
