"""Independent check of the similarity signal, end to end through fusion.

Builds scam and legit messages from fragments written separately from the
reference corpus (different wording, slang, typos, mixed case), so a pass
means the signal generalises instead of recognising its own examples. Call
features are calm and there's no identity history, so the result shows what
similarity catches on its own.

Run: PYTHONPATH=src python3 scratch/similarity_check.py [seed]
"""
import json
import sys

import numpy as np

from trustgraph.fusion import BANDS_PATH, risk_band
from trustgraph.pipeline import score_interaction

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
rng = np.random.default_rng(SEED)
BANDS = json.load(open(BANDS_PATH))
CALM = {"duration_sec": 100, "hour_of_day": 12, "amount_ratio": 1.0,
        "contact_freq_24h": 1, "urgency_score": 0, "new_channel_flag": 0}
results = []
print(f"seed {SEED}")


def check(name, passed, detail):
    results.append(passed)
    print(f"  [{'PASS' if passed else 'FAIL'}] {name}: {detail}")


def pick(options):
    return str(rng.choice(options))


def noisy(text):
    """Real messages are messy: random case, dropped apostrophes, doubled spaces."""
    if rng.random() < 0.2:
        text = text.lower()
    if rng.random() < 0.2:
        text = text.replace("'", "")
    if rng.random() < 0.1:
        text = text.upper()
    return text


# Each scam = pretext + ask (+ optional pressure). Fragments are new wording.
SCAMS = {
    "safe account": (
        ["Hi, Mark from the security desk at your bank here.", "Fraud prevention team calling about your current account.",
         "We've flagged unusual logins on your account from abroad."],
        ["To keep your money protected, shift everything into the secure account we opened for you.",
         "Please move the funds to a new safe account while we lock the old one.",
         "Transfer your balance over to the holding account number I'm about to read out."]),
    "one-time code": (
        ["Security check on your account.", "We're stopping a payment someone tried to make.", "Quick verification needed."],
        ["Can you read out the code we've just texted you?", "Please tell me the 6-digit code that just arrived by SMS.",
         "Give me the passcode your bank sent so I can block it."]),
    "gift cards": (
        ["Hey, you around? In back to back meetings.", "Need a quick favour, can't call right now.", "It's the MD, urgent task for you."],
        ["Pop out and buy four Apple gift cards, then send me the codes on the back.",
         "Grab some Amazon cards for a client thank-you and text me the card numbers.",
         "Get 3 Steam cards from the shop and send photos of the codes."]),
    "remote access": (
        ["Tech support here, your laptop is reporting a virus to us.", "Your broadband has been compromised.",
         "We're calling about the refund you're owed."],
        ["Download AnyDesk and read me the number so I can fix it.", "I'll need remote access to your PC to sort it out.",
         "Open TeamViewer and let me connect to your screen."]),
    "bank details changed": (
        ["Hope you're well.", "Following up on the outstanding invoice.", "Quick update from our accounts team."],
        ["Our bank details have changed, so please pay the invoice to the new account attached.",
         "Please remit payment to our updated bank account below, not the old one.",
         "We've moved banks, pay to the new account in this email from now on."]),
    "crypto": (
        ["My trading coach got me 40% last month.", "There's a new token launching this week.", "Guaranteed returns, zero risk."],
        ["Send some bitcoin to this wallet address and I'll set you up.", "Transfer USDT to my wallet and I'll invest it for you.",
         "Buy crypto and send it to the wallet below to join."]),
    "tax threat": (
        ["Official notice regarding unpaid tax.", "This call is from the revenue office.", "Final warning about your tax account."],
        ["A warrant will be issued for your arrest unless you pay today.", "Pay the outstanding amount now to avoid legal action.",
         "Settle this immediately or court proceedings will begin."]),
}
# Scams with no concrete ask a pattern can see: only the wording can help.
WORDING_ONLY = {
    "hi mum": ["hi mum its me, this is my new number, old phone smashed. can u help me pay something today",
               "Mum, new phone new number! Got a bill I need paying today and my app isnt working, can you help?",
               "hey dad using a mates phone, need to pay my rent today or im out, can u transfer it"],
    "romance": ["Darling I can't wait to finally meet you, but I can't afford the flight. Could you help with the ticket?",
                "My love, my bank account is frozen while I'm working overseas. Can you send me some money to get by?",
                "You're the only one I trust. My son is in hospital and I need help with the bills, please send what you can."],
}
PRESSURE = ["", " Please do it now.", " Don't tell anyone about this, it's confidential.", " This is urgent."]

LEGIT = [
    "Your login code is {n}. Don't share it with anyone.", "{n} is your verification code. We will never call to ask for it.",
    "Reminder: your bank will never ask you to move money into a safe account.",
    "Invoice {n} is attached, due end of the month to the usual account.",
    "It's {name} on a new number, save it! Drinks Friday?", "Got a new phone, this is {name}. See you at the match.",
    "Can you pick up milk and bread on the way home?", "Meeting moved to 3pm, same room.",
    "Thanks for the gift card, I'm going to spend it on books!", "Don't tell {name} but I booked us a surprise trip!",
    "The report is attached, let me know what you think.", "Parcel delivered to your safe place (porch).",
    "Your subscription payment of 9.99 was successful.", "We've updated our terms. No action needed.",
    "Happy anniversary! Dinner's booked for 8.", "Can you send me the photos from the weekend?",
    "The plumber quoted 120 for the leak, ok to go ahead?", "Your tax return was received, no further action needed.",
    "Car's booked in for a service Tuesday.", "Could you cover my 2pm call? Notes are in the shared doc.",
]
NAMES = ["Sam", "Priya", "Tom", "Aisha", "Kofi", "Elena"]


def scam_message(pretexts, asks):
    return noisy(f"{pick(pretexts)} {pick(asks)}{pick(PRESSURE)}")


def band(text):
    return risk_band(score_interaction({**CALM, "message_text": text})[1].score, BANDS)


print("1. Legit messages, including ones that share scam vocabulary (1000)")
legit = [noisy(pick(LEGIT).format(n=rng.integers(1000, 999999), name=pick(NAMES))) for _ in range(1000)]
flagged = [m for m in legit if band(m) != "Low"]
check("legit messages stay within the 5% budget", len(flagged) / len(legit) <= 0.05, f"{len(flagged) / len(legit):.1%} flagged")
for m in sorted(set(flagged))[:5]:
    print(f"     flagged: {m}")

print()
print("2. Scams with a concrete ask, in new wording (200 each)")
for name, (pretexts, asks) in SCAMS.items():
    rate = float(np.mean([band(scam_message(pretexts, asks)) != "Low" for _ in range(200)]))
    check(f"{name} caught", rate >= 0.95, f"{rate:.1%}")

print()
print("3. Scams with no concrete ask (wording only, reported, not a target)")
for name, messages in WORDING_ONLY.items():
    rate = float(np.mean([band(noisy(pick(messages))) != "Low" for _ in range(200)]))
    print(f"     {name}: {rate:.0%} reach Caution on wording alone; needs another signal to agree")

print()
print(f"{sum(results)}/{len(results)} checks passed")
