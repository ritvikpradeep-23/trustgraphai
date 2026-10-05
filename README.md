<p align="center">
  <img src="https://github.com/Runa8147/Hackathena_Readme_Template/blob/d0add823684f0ac28b76a99636c729f80b0ca8ff/hackathena_banner.png" alt="Hackathena '26 2.0" width="100%">
</p>

<h1 align="center">TrustGraph</h1>

<p align="center">
  <strong>Scores a message, call or video for AI-assisted fraud, and explains why in plain words.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Hackathena-'26%202.0-black?style=for-the-badge" alt="Hackathena">
  <img src="https://img.shields.io/badge/Theme-AI%20Fraud%20Detection-red?style=for-the-badge" alt="Theme">
  <img src="https://img.shields.io/badge/Status-Prototype-white?style=for-the-badge&labelColor=black" alt="Status">
</p>

---

## 👥 Team

**Team Name:** `[TEAM NAME]`

| Member     | Role      | Institution |
| ---------- | --------- | ----------- |
| **[Name]** | Team Lead | [College]   |
| **[Name]** | [Role]    | [College]   |
| **[Name]** | [Role]    | [College]   |
| **[Name]** | [Role]    | [College]   |

---

## 🎯 Problem Statement

The rapid advancement of generative AI has made it increasingly difficult to distinguish authentic content from artificially generated or manipulated content.

Deepfakes, cloned voices, synthetic images, fabricated documents, and other AI-assisted techniques can enable **impersonation, misinformation, identity theft, financial fraud, and social engineering attacks**.

Scammers now write convincing messages with AI (fake bank alerts, "digital arrest" threats, KYC expiry notices,
boss gift-card requests, AI voice-clone family emergencies) in English, Hinglish and Manglish, and back them with
deepfake video calls. People get little warning before they pay or share a code.

---

## 💡 Solution

### TrustGraph

**TrustGraph** is a **web + API** solution designed to detect **AI-assisted scam messages, impersonation and
deepfake videos**.

The system takes **a message (plus optional call details or an MP4 video)**, analyzes it with **several independent
signals (anomaly detection, identity continuity, scam-wording similarity, a report history and a deepfake video
pipeline)**, and produces **a Low / Caution / High risk level with a plain-language explanation** to help users
identify potentially fraudulent content.

### Key Features

* 🔴 **Explainable risk score**: every verdict names the signal that drove it ("asks for a one-time code", "reads like a known gift-card scam").
* ⚪ **Identity continuity**: flags a contact whose bank account, email domain or phone number suddenly changed (look-alike domains too).
* ⚫ **Scam-report matching**: a new message is compared with messages people already reported, without ever revealing another user's report.
* 🔴 **Deepfake video check**: samples frames, finds the face, scores it with a pluggable model, and says "inconclusive" when no face is visible instead of guessing.
* ⚪ **Hinglish and Manglish**: tested on Indian-English code-mixed scams, not just English.

---

## 🔄 How It Works

```text
            website / browser extension / (future) messaging bots
                                   |
                                   v
        +------------------- TrustGraph API (FastAPI) -------------------+
        |                                                                 |
        |  text ---> normalize ---> embed (MiniLM) ---> match reports ----+--> LOW / MEDIUM / HIGH + evidence ids
        |                                                                 |
        |  video --> validate MP4 -> 1 frame/s -> largest face -> model --+--> likely_fake / likely_real / inconclusive
        +-----------------------------------------------------------------+

        Detector engine (src/trustgraph), used by the demo website:
          anomaly (Isolation Forest) + continuity (rules) + similarity (TF-IDF + red flags)
          + precedent (report lookup)  --noisy-OR-->  Low / Caution / High + explanation
```

![System Architecture](ARCHITECTURE_IMAGE_URL)

*System architecture and processing workflow.*

---

## 🛠️ Technology Stack

### Software

| Layer          | Technologies |
| -------------- | ------------ |
| **Frontend**   | HTML / CSS / JavaScript demo page (`src/trustgraph/web/index.html`) |
| **Backend**    | FastAPI (`app/`), plus a small standard-library server for the demo page |
| **AI / ML**    | scikit-learn (Isolation Forest, TF-IDF, logistic regression), sentence-transformers all-MiniLM-L6-v2, PyTorch (TorchScript deepfake model slot) |
| **Database**   | JSON file behind a small repository interface (ready to swap for pgvector) |
| **Processing** | OpenCV, NumPy, pandas |
| **Deployment** | Local (`uvicorn`); no cloud deployment yet |

### Tools

* Git & GitHub
* pytest (about 150 automated tests)
* Claude Code

---

## 📸 Project Preview

### Main Interface

![Main Interface](SCREENSHOT_1_URL)

*Main interface of the application.*

### Detection / Analysis

![Detection](SCREENSHOT_2_URL)

*AI fraud detection and analysis workflow.*

### Results

![Results](SCREENSHOT_3_URL)

*Detection result, risk assessment, and supporting information.*

---

## 📊 Results

> **All detection numbers below come from synthetic (AI-written) test messages**, except the real-SMS row. They show
> how the engine behaves on that data, **not real-world accuracy**.

| Metric | Result |
| ------ | ------ |
| **Scams caught, frozen synthetic test** (2,294 messages, 29 scam types, text only) | **74.0%**, with 8.6% of honest messages flagged |
| **Scams caught, final test of the 10-round improvement routine** (rounds 13-14, used once) | **65.0%** (starting engine 51.7%), with 0.0% of honest messages flagged |
| **Real UK text messages wrongly flagged** (4,827 honest SMS, public dataset) | **3.6-9.6%** depending on the version |
| **Named demo scenarios** | 18/18 scams flagged, 6/6 honest controls kept Low |
| **Supported input** | Text messages, call/interaction details, MP4 video (deepfake model must be supplied) |

Full reports: `reports/2026-10-05-casual/CHANGES.md`, `reports/fast/final_summary.md`,
`reports/2026-10-05-training/training_summary.md`.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.11 or newer
* Internet on the first run (downloads the ~90 MB text-embedding model once)
* No API keys

### Installation

```bash
git clone https://github.com/ritvikpradeep-23/trustgraphai.git
cd trustgraphai

pip install -r requirements.txt
```

### Environment Variables

All optional. Copy `.env.example` to `.env` to change them:

```env
SCAM_HIGH_THRESHOLD=0.82
SCAM_MEDIUM_THRESHOLD=0.68
DEEPFAKE_MODEL_PATH=models/deepfake.pt
CORS_ORIGINS=http://localhost:3000,chrome-extension://<your extension id>
```

### Run

```bash
python run_website.py                       # demo page: http://127.0.0.1:8000
python scripts/seed_reports.py              # 10 example scam reports for the API
python -m uvicorn app.main:app --port 8001   # API: http://127.0.0.1:8001/docs
```

The application will be available at:

```text
http://127.0.0.1:8000 (demo page)   http://127.0.0.1:8001/docs (API)
```

---

## 🎥 Demo

### Live Demo

**[LIVE DEMO URL]**

### Demo Video

**[DEMO VIDEO URL]**

> The demo demonstrates the complete workflow from input submission to fraud detection, analysis, and final result.

---

## 🧪 Example

**Input**

```text
Hi, it's the CEO. I'm in a board meeting and can't talk. Buy four Apple gift cards for a client
and send me the codes on the back. Keep this between us.
```

**System Analysis**

```text
Combined score 0.93; driven by 'similarity' (score 0.93): reads like a known gift-card request from a
boss or colleague script (similarity 0.48); asks for gift-card codes; asks to keep it secret
```

**Result**

```text
SUSPICIOUS
Score: 0.93
Risk Level: HIGH
```

---

## 🔐 Security & Privacy

The system is designed with user privacy and responsible AI usage in mind.

* Uploaded videos go to a temporary file and are deleted after analysis, even when analysis fails.
* Analyzing a message never stores it. Only messages a user explicitly reports are kept.
* The API never returns another user's report text: matches come back as id, similarity and source only.
* Logs record ids, lengths and sources, never message text.
* No deepfake score is ever invented: without a model the API says `model_not_configured`, and the demo mock labels every answer `"mock": true`.
* No API keys or credentials are needed; settings come from environment variables.

---

## 🔮 Future Scope

* [ ] Train and add a real deepfake model (EfficientNet-B0 backbone; see `docs/TRUSTGRAPH_DETAILS.md`)
* [ ] Replace synthetic test data with real reported scams and real honest messages
* [ ] Browser extension and Telegram/WhatsApp adapters (interface ready in `app/integrations/base.py`)
* [ ] Move scam reports to PostgreSQL + pgvector
* [ ] Voice-clone detection for calls

---

## 👨‍💻 Team Contributions

* **[Member 1]** — [Architecture / AI model / Backend / etc.]
* **[Member 2]** — [Frontend / UI / Integration / etc.]
* **[Member 3]** — [Dataset / ML / Testing / etc.]
* **[Member 4]** — [Research / Documentation / Deployment / etc.]

---

## 🏆 Hackathena '26 2.0

This project was developed as part of **Hackathena '26 2.0**, organized by the **Department of Computer Science & Engineering and CESA, Jyothi Engineering College**.

### Theme

> **Detection and Prevention of AI-Based Frauds**

The project focuses on addressing emerging forms of fraud enabled or amplified by generative artificial intelligence, including **deepfakes, cloned voices, synthetic media, fabricated documents, and AI-assisted impersonation**.

---

## 📄 Repository Structure

The code keeps the layout it was built and tested in. This is how it maps to the template's folders:

```text
.
├── app/                   # Backend: TrustGraph API (FastAPI): text matching + deepfake video
├── src/trustgraph/        # Detector engine (four signals + fusion)
│   └── web/               # Frontend: demo page (index.html) and its small server
├── models/                # AI/ML models (detector files, candidate bundles, deepfake model slot)
├── data/                  # Sample / synthetic data (incl. data/rounds for the improvement routine)
├── eval/                  # Synthetic evaluation set, generator, metrics
├── training/  routine/    # Training experiments and the 10-round improvement routine
├── reports/               # Results (all marked synthetic where they are)
├── docs/                  # Documentation (TRUSTGRAPH_DETAILS.md)
├── scripts/               # Seed, promote/rollback, round and final-test scripts
├── tests/                 # Automated tests (pytest)
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── README.md
```

---

## 📬 Contact

For questions, collaboration, or further information:

**Team:** [TEAM NAME]
**Team Lead:** [NAME]
**Email:** [EMAIL]
**GitHub:** https://github.com/ritvikpradeep-23/trustgraphai

---

<p align="center">

<strong>Hackathena '26 2.0</strong>

<br>

Detection & Prevention of AI-Based Frauds

<br><br>

<img src="https://img.shields.io/badge/Built%20at-Jyothi%20Engineering%20College-black?style=flat-square">
<img src="https://img.shields.io/badge/Hackathena-2026-red?style=flat-square">

</p>
