"""Add about 10 realistic example scam reports so the demo has data to match against.

    python scripts/seed_reports.py

Uses the same settings as the server (REPORTS_PATH etc.). Running it twice
doesn't create duplicates. All examples are invented: fictional banks and
brands, placeholder links, no real numbers or people.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.config import get_settings  # noqa: E402
from app.scam_engine.embedder import Embedder  # noqa: E402
from app.scam_engine.repository import InMemoryReportRepository  # noqa: E402
from app.scam_engine.service import ScamService, normalize_text  # noqa: E402

EXAMPLES = [
    # bank account suspension
    "Dear customer, your Lotus Bank account has been suspended due to unusual activity. Verify your identity "
    "within 24 hours at the link below or your account will be permanently closed.",
    # KYC expiry
    "Your KYC has expired and your account will be blocked today. Update your PAN and Aadhaar details now at "
    "the link and enter the OTP you receive to keep your account active.",
    # courier / customs fee
    "Your parcel is held at customs. Pay the clearance fee of Rs 49 at the link within 12 hours or it will "
    "be returned to the sender.",
    # prize / lottery
    "Congratulations! Your number won Rs 25 lakh in the lucky draw. Pay the processing fee first to release "
    "your prize money.",
    # job with upfront fee
    "You are selected for the work-from-home data entry job, Rs 30,000 a month. Pay the registration fee "
    "today to receive your offer letter.",
    # electricity disconnection
    "Dear consumer, your electricity will be disconnected tonight at 9.30 pm because last month's bill is not "
    "updated. Call our officer immediately on the number below.",
    # OTP / account takeover
    "Hi, I sent my verification code to your number by mistake. Can you forward me the 6 digit code you just "
    "received? It's urgent.",
    # family emergency, new number
    "Mum, this is my new number, I lost my phone. I need to pay a bill urgently, can you transfer the money "
    "to this account? Please don't tell Dad.",
    # UPI refund / collect request
    "Your refund of Rs 1,500 is ready. Approve the payment request in your UPI app and enter your PIN to "
    "receive the money.",
    # investment group
    "Join our VIP trading group, our AI bot made 300% this month. Deposit just Rs 5,000 to start and "
    "withdraw guaranteed profit daily.",
]


def main():
    settings = get_settings()
    service = ScamService(Embedder(settings.embedding_model_name),
                          InMemoryReportRepository(settings.reports_path), settings)
    added = 0
    for text in EXAMPLES:
        if service.repository.contains_text(normalize_text(text)):
            continue  # already seeded
        service.report(text, source="seed")
        added += 1
    print(f"Added {added} example reports ({service.repository.count()} stored in {settings.reports_path}).")


if __name__ == "__main__":
    main()
