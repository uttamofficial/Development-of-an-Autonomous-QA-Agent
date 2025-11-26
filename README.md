# Autonomous QA Agent for Test Case and Script Generation

An intelligent QA automation tool that uses Retrieval-Augmented Generation (RAG) to generate test cases from documentation and automatically create executable Selenium test scripts.

## 🎯 Project Overview

This project implements an autonomous QA agent that:

- **Ingests** support documents (markdown, text, JSON, PDF) and HTML checkout pages
- **Builds** a knowledge base using vector embeddings (ChromaDB)
- **Generates** test cases using RAG, ensuring all outputs are grounded in provided documentation
- **Creates** executable Selenium Python scripts with real selectors extracted from HTML

The system is designed to prevent hallucinations by strictly grounding all generated content in the uploaded documents, making it suitable for production QA workflows.

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework for building APIs
- **Uvicorn** - ASGI server for running FastAPI
- **ChromaDB** - Vector database for storing document embeddings
- **Sentence Transformers** - Embedding model for document vectorization
- **OpenAI API** - LLM for test case and script generation
- **Pydantic** - Data validation and settings management
- **PyMuPDF** - PDF document parsing
- **BeautifulSoup4** - HTML parsing and selector extraction

### Frontend
- **Streamlit** - Interactive web UI for user interactions
- **Requests** - HTTP client for API communication

### Testing
- **Selenium** - WebDriver for automated test scripts

## 📋 Prerequisites

- **Python 3.9+** (Python 3.10 or 3.11 recommended)
- **OpenAI API Key** (or compatible LLM API key)
- **Git** (for cloning the repository)

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd "Ocean AI"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** The first installation may take several minutes as it downloads embedding models and dependencies.

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=gpt-4
VECTOR_DB_PATH=data/vector_db
```

**Important:** Replace `your_openai_api_key_here` with your actual OpenAI API key.

### 5. Run the Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at `http://localhost:8000`

API documentation (Swagger UI) is available at `http://localhost:8000/docs`

### 6. Run the Frontend

In a new terminal (with virtual environment activated):

```bash
streamlit run frontend/streamlit_app.py
```

The frontend will open in your browser at `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Upload Documents

1. **Upload Support Documents**
   - Click "Browse files" in the "Support Documents" section
   - Select one or more files (`.md`, `.txt`, `.json`, `.pdf`)
   - Example files are provided in `assets/` folder:
     - `product_specs.md` - Product specifications and feature rules
     - `ui_ux_guide.txt` - UI/UX guidelines and styling rules
     - `api_endpoints.json` - API endpoint documentation

2. **Upload Checkout HTML**
   - Click "Browse files" in the "Checkout HTML" section
   - Select `checkout.html` file (example provided in `assets/checkout.html`)
   - This file contains the actual HTML structure for selector extraction

3. **Click "Upload Files"**
   - Wait for upload confirmation
   - Files are saved to `data/uploaded_docs/` and `data/html/`

### Step 2: Build Knowledge Base

1. Click the **"Build Knowledge Base"** button
2. The system will:
   - Parse all uploaded documents
   - Chunk the content into manageable pieces
   - Generate embeddings using sentence transformers
   - Store everything in ChromaDB vector database
3. Review the summary showing:
   - Total documents processed
   - Total chunks created
   - Any errors encountered

### Step 3: Generate Test Cases

1. **Enter a Test Case Request** in the text area
   - Example: `"Generate all positive and negative test cases for the discount code feature."`
   - Be specific about features and test types you want
2. Click **"Generate Test Cases"**
3. The system will:
   - Query the knowledge base for relevant information
   - Use RAG to generate test cases grounded in your documents
   - Display all generated test cases
4. **Select a Test Case** from the dropdown to view details:
   - Test ID, Feature, Scenario
   - Preconditions, Steps, Expected Result
   - Source documents (showing which docs it's based on)

### Step 4: Generate Selenium Script

1. **Select a test case** from the dropdown (from Step 3)
2. Review the test case details displayed
3. Click **"Generate Selenium Script"**
4. The system will:
   - Parse `checkout.html` to extract real selectors
   - Query knowledge base for relevant documentation
   - Generate a complete, executable Python Selenium script
5. **View the Script** in the code block
6. **Download** the script using the download button

## 📚 Support Documents

The project includes example support documents in the `assets/` folder:

### `product_specs.md`
- **Purpose:** Product specifications and feature rules
- **Contents:**
  - Discount code rules (SAVE10, SAVE15, SAVE20, WELCOME)
  - Shipping method specifications (Standard: free, Express: $10)
  - Payment method details (Credit Card, PayPal)
  - Pricing calculation rules
  - Form validation requirements
  - Cart management rules

### `ui_ux_guide.txt`
- **Purpose:** UI/UX design guidelines
- **Contents:**
  - Form validation error display rules (red text)
  - Button styling (Pay Now button: green)
  - Success message formatting
  - Layout and spacing guidelines
  - Color consistency rules
  - Interactive element specifications

### `api_endpoints.json`
- **Purpose:** API endpoint documentation
- **Contents:**
  - REST API endpoint definitions
  - Request/response schemas
  - Validation rules
  - Error codes and handling

### `checkout.html`
- **Purpose:** Example checkout page HTML
- **Contents:**
  - Complete checkout form with all required elements
  - Form fields with clear IDs and names for Selenium
  - Discount code input
  - Shipping and payment method radio buttons
  - Validation and success message handling

## 🔒 Knowledge Grounding

**Critical Feature:** This system is designed to prevent hallucinations by strictly grounding all outputs in provided documentation.

### How It Works:

1. **Document Ingestion:** All uploaded documents are parsed and chunked
2. **Vector Storage:** Chunks are embedded and stored in ChromaDB
3. **RAG Query:** When generating test cases:
   - Relevant chunks are retrieved from the knowledge base
   - Only information from these chunks is used
   - LLM is explicitly instructed to use ONLY provided context
4. **Source Attribution:** Each test case includes a `grounded_in` field listing source documents
5. **Selector Extraction:** Selenium scripts use ONLY selectors that exist in the provided HTML

### Benefits:

- ✅ No invented features or requirements
- ✅ Test cases reference actual documentation
- ✅ Selenium scripts use real HTML selectors
- ✅ Traceable source attribution
- ✅ Production-ready, reliable outputs

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Required
OPENAI_API_KEY=your_api_key_here

# Optional (with defaults)
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
LLM_MODEL=gpt-4
VECTOR_DB_PATH=data/vector_db
CHROMA_COLLECTION_NAME=qa_agent_kb
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
UPLOADED_DOCS_PATH=data/uploaded_docs
HTML_PATH=data/html
```

### Backend Configuration

Backend settings are managed through `backend/core/config.py` using Pydantic Settings. All settings can be overridden via environment variables.

### Frontend Configuration

The frontend allows you to configure the backend API URL via the sidebar. Default: `http://localhost:8000/api`

## 📁 Project Structure

```
Ocean AI/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   └── routes.py          # API endpoints
│   ├── services/
│   │   ├── ingestion_service.py    # Document ingestion
│   │   ├── rag_service.py          # RAG-based test case generation
│   │   └── selenium_service.py     # Selenium script generation
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   ├── vector_store.py    # ChromaDB wrapper
│   │   ├── llm_client.py      # LLM client wrapper
│   │   ├── chunking.py        # Document chunking utilities
│   │   └── parsers.py         # Document parsers
│   └── models/
│       └── test_case.py        # Pydantic models
├── frontend/
│   └── streamlit_app.py       # Streamlit UI
├── data/
│   ├── uploaded_docs/         # Uploaded support documents
│   ├── html/                  # Uploaded HTML files
│   └── vector_db/             # ChromaDB persistent storage
├── assets/
│   ├── checkout.html          # Example checkout page
│   ├── product_specs.md       # Example product specs
│   ├── ui_ux_guide.txt        # Example UI/UX guide
│   └── api_endpoints.json     # Example API docs
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Limitations & Notes

### Current Limitations:

1. **LLM Dependency:** Requires OpenAI API key (or compatible LLM API)
2. **Model Size:** First run downloads embedding model (~400MB)
3. **Processing Time:** Large documents may take time to process
4. **HTML Parsing:** Selenium scripts are generated based on the provided HTML structure
5. **Single HTML:** Currently processes one checkout.html file at a time

### Best Practices:

1. **Document Quality:** Provide clear, well-structured documentation for best results
2. **HTML Completeness:** Ensure checkout.html includes all form elements with proper IDs/names
3. **Test Case Queries:** Be specific in test case requests for better results
4. **Knowledge Base:** Rebuild knowledge base after uploading new documents
5. **API Keys:** Never commit `.env` file with API keys to version control

### Troubleshooting:

- **Backend won't start:** Check if port 8000 is available
- **Frontend can't connect:** Verify backend is running and URL is correct
- **No test cases generated:** Ensure knowledge base is built and contains relevant content
- **Selenium script errors:** Verify checkout.html is uploaded and contains required elements
- **Import errors:** Ensure virtual environment is activated and dependencies are installed

## 🧪 Testing the System

1. **Upload example documents** from `assets/` folder
2. **Build knowledge base** and verify document count
3. **Generate test cases** with query: "Generate test cases for discount code validation"
4. **Select a test case** and generate Selenium script
5. **Review generated script** to verify it uses real selectors from checkout.html

## 📝 License

This project is developed as part of a take-home assignment.

## 🤝 Contributing

This is an assignment project. For questions or issues, please refer to the assignment guidelines.

---

**Built with ❤️ using FastAPI, Streamlit, and RAG technology**
