# 🧾 Invoice Processing Pipeline

An end-to-end automated pipeline for extracting, validating, mapping, and reviewing GST invoices with Streamlit Dashboard support.

---

## 🚀 Features

* **Ingestion** → Extracts text & QR payloads from PDF invoices.
* **Validation** → Validates invoice data against QR payloads using LLM.
* **Logger** → Logs structured data into Excel sheets.
* **Mapper** → Maps invoice line items with master product data.
* **GST Fetcher** → Fetches GST rates from online sources or local cache.
* **Reviewer** → Cross-checks totals, GST calculations, and flags mismatches.
* **Streamlit Dashboard** → Upload invoices, monitor progress, and download results via a user-friendly UI.

---

## 📂 Project Structure

```
Invoice_agent/
│-- agents/                # All pipeline agents
│   ├── ingestion_agent.py
│   ├── validation_agent.py
│   ├── logger_agent.py
│   ├── mapper_agent.py
│   ├── gst_fetcher_agent.py
│   ├── reviewer_agent.py
│
│-- data/
│   ├── invoices/          # Upload invoices here
│   └── outputs/           # Extracted text & final Excel output
│
│-- .env                   # Environment variables (API keys, configs)
│-- Api.py                 # API wrapper for external services
│-- app.py                 # Alternative app entry point (if required)
│-- pipeline.py            # Orchestrates the entire pipeline
│-- requirements.txt       # Python dependencies
│-- streamlit_app.py       # Streamlit Dashboard
│-- README.md              # Project documentation
```

---

## Installation

Clone the repository and set up the environment:

```bash
# Clone repository
git clone https://github.com/<your-username>/invoice-processing-agent.git
cd invoice-processing-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate   # (Windows)
source venv/bin/activate # (Linux/Mac)

# Install dependencies
pip install -r requirements.txt
```

---

## ▶️ Usage

### Run the pipeline (CLI mode)

```bash
python pipeline.py
```

### Run with API service

```bash
python Api.py
```

### Run the dashboard (UI mode)

```bash
streamlit run streamlit_app.py
```

---

## 📊 Output

* Consolidated Excel file: `data/outputs/invoices_data.xlsx`
* Validation flags, GST fetch results, and review reports stored inside Excel sheets.

---

## 🤝 Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## 📜 License

This project is licensed under the MIT License.
