# ai-model

TrustGraph: scores an interaction (a call, text or email) for scam risk and explains why.

| Signal | Asks | Status |
|---|---|---|
| Anomaly | Does the call behave oddly? (3am, huge amount, many urgent words) | built |
| Continuity | Have the contact's details changed? (new bank account, lookalike email domain) | built |
| Similarity | Does the message read like a known scam? (gift-card codes, "safe account") | built |
| Precedent | Has this number, account, link or wallet been reported as a scam before? | built (demo report list) |

The signals combine into one risk level: **Low**, **Caution** or **High**.

## Try it in your browser

**Windows:** install [Python 3.12](https://www.python.org/downloads/) (tick "Add python.exe to PATH"), then double-click `start_website.bat`.

**Any system:**

```bash
pip install -r requirements.txt
python run_website.py
```

A page opens at http://127.0.0.1:8000. Pick an example from the menu or type your own, then press **Check risk**. It runs only on your computer.

## Run the checks

```bash
python -m pytest tests/                          # unit tests
PYTHONPATH=src python -m trustgraph.evaluate     # named scenarios + false-alarm rate
PYTHONPATH=src python scratch/similarity_check.py 99   # independent check, any seed
```
