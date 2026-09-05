# PatentLens AI

> **AI-Powered Semantic Prior-Art Discovery for Innovators**

PatentLens AI is an end-to-end, AI-powered patent prior-art search platform designed for MSME innovators, students, researchers, startups, and independent inventors. It enables users to perform preliminary semantic prior-art discovery by analyzing invention descriptions, computing 384-dimensional vector embeddings via Sentence Transformers (`all-MiniLM-L6-v2`), searching patent vector indexes, and generating hybrid similarity risk scores.

---

## ⚠️ Important Legal Disclaimer

> *"PatentLens AI provides AI-assisted preliminary prior-art search results for informational and research purposes only. The results do not constitute legal advice, a patentability determination, or a professional patent opinion."*

---

## 🚀 Key Features

* **Semantic Patent Search**: Finds conceptually and technically similar patent documents using SBERT neural vector representations rather than keyword matching alone.
* **Hybrid Similarity Algorithm**: Combines $70\%$ Semantic Similarity, $20\%$ Keyword & Concept Overlap, and $10\%$ Technology Domain Alignment.
* **AI Concept Overlap Detection**: Extracts and highlights overlapping technical concepts (e.g. *Machine Learning*, *Soil Moisture*, *Sensors*, *Automation*).
* **Prior-Art Risk Classification**: Categorizes findings into `LOW` ("Potentially Distinct"), `MODERATE` ("Further Review Recommended"), `HIGH` ("Strong Similarities Found"), and `VERY HIGH` ("Potentially Significant Prior Art").
* **Interactive Analytics & Recharts**: Visualizes similarity distributions and top matching patent scores with responsive charts.
* **AI-Assisted PDF Reports**: Generates downloadable PDF research reports with branding, metadata, top 5 matches, and disclaimers.
* **Search History & Saved Patents**: Allows users to save patents, add personal research notes, and revisit past search trajectories.
* **User Authentication & Ownership**: Secure JWT access & refresh token authentication, bcrypt password hashing, and user-isolated database ownership checks.
* **Demo Dataset Badge**: Clearly displays **"Demo Dataset"** in the UI when operating on local sample technical records (100 documents across 10 technology domains).

---

## 🛠️ Technology Stack

### Frontend
* **Framework**: Next.js 14 (App Router, TypeScript)
* **Styling**: Tailwind CSS
* **Icons & Animations**: Lucide React, Framer Motion
* **Analytics Charts**: Recharts

### Backend & AI Processing
* **API Framework**: Python FastAPI (REST API architecture)
* **ML / Embedding Model**: Sentence Transformers (`all-MiniLM-L6-v2`, 384-d normalized vectors loaded ONCE at startup)
* **Concept Extractor**: TF-IDF & N-gram Technical Phrase Extraction
* **PDF Report Generator**: ReportLab

### Database & Vector Engine
* **Database**: PostgreSQL with `pgvector` extension (or local SQLite vector fallback adapter)
* **ORM**: SQLAlchemy

---

## 🚀 How to Run the Application

### 1️⃣ Terminal 1 — Start FastAPI Backend Server
```powershell
cd "d:\patent prior ART\backend"
python main.py
```
> ℹ️ *FastAPI REST API runs at **`http://localhost:8000`** (API docs available at **`http://localhost:8000/docs`**).*

---

### 2️⃣ Terminal 2 — Start Next.js Frontend App
```powershell
cd "d:\patent prior ART\frontend"
npm run dev
```
> ℹ️ *Next.js frontend runs at **`http://localhost:3000`**.*

---

### 🌐 Open in Browser:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## 🔒 Security Features

* **Password Security**: Passwords hashed using native `bcrypt` (never stored as plain text).
* **JWT Tokens**: Short-lived access tokens with HTTP-only refresh tokens.
* **User Authorization**: Strict backend ownership verification on searches, saved patents, reports, and profile resources.
* **Input Validation**: Pydantic v2 schemas validating request parameters and character limits.

---

## 📄 License & Disclaimer

PatentLens AI is developed for research and demonstration purposes. Demo Dataset records do not constitute verified official USPTO/EPO patent filings.
