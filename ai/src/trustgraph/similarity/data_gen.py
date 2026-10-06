"""Synthetic legit message text for calibration, assembled from parts that
don't appear in the reference corpus, so the similarity signal isn't scored
on messages it already holds. About 30% of interactions carry no text (e.g. a
call with no transcript); ~8% of the rest are "tricky" legit messages that
share scam vocabulary (2FA codes, new numbers, invoices, secrets, fees).
"""
import json

import numpy as np

OPENERS = ["Hi", "Hey", "Hello", "Morning", "Hi there", "Afternoon", ""]
NAMES = ["Sam", "Priya", "Tom", "Aisha", "Marco", "Chen", "Olu", "Sara", "team", "all"]
BODIES = [
    "are we still on for {day}?",
    "the {thing} is ready, I'll drop it round on {day}.",
    "can you send over the {thing} when you get a chance?",
    "thanks for sorting the {thing}, really appreciate it.",
    "just confirming the {thing} for {day} at {time}.",
    "I'll be a bit late on {day}, start without me.",
    "please review the attached {thing} before {day}.",
    "the {thing} has been updated, have a look when you can.",
    "can we push the {thing} to {day}? Something came up.",
    "great to see you yesterday, let's do it again soon.",
    "your {thing} has been booked for {day} at {time}.",
    "quick question about the {thing}, call me when free.",
]
TRICKY = [
    "Your sign-in code is {code}. It expires in 5 minutes. Don't share it with anyone.",
    "It's {name}, new phone so new number. See you {day}!",
    "Invoice {code} for the {thing} is attached, payable to the usual account by {day}.",
    "Keep it quiet but we're planning a surprise for {name} on {day}!",
    "The late fee on the library books is 2 pounds, can you drop it in {day}?",
    "Got {name} a gift card for her birthday, can you sign the card too?",
    "Reminder from your bank: we'll never ask you to transfer money to a safe account.",
    "Your parcel with the {thing} will be delivered {day} between {time} and 5pm.",
]
THINGS = ["report", "quote", "rota", "slides", "invoice", "contract", "booking", "car", "keys", "plan", "order", "menu"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "the weekend", "tomorrow", "next week"]
TIMES = ["9am", "10:30", "noon", "2pm", "3:15", "4pm"]
CLOSERS = ["Thanks!", "Cheers", "See you then.", "x", "Best,", "", "Speak soon."]


def legit_message(rng) -> str | None:
    if rng.random() < 0.30:
        return None
    fill = {"day": rng.choice(DAYS), "thing": rng.choice(THINGS), "time": rng.choice(TIMES),
            "name": rng.choice(NAMES[:8]), "code": int(rng.integers(1000, 999999))}
    if rng.random() < 0.08:
        return str(rng.choice(TRICKY)).format(**fill)
    opener = str(rng.choice(OPENERS))
    greeting = f"{opener} {rng.choice(NAMES)}, " if opener else ""
    body = str(rng.choice(BODIES)).format(**fill)
    return f"{greeting}{body} {rng.choice(CLOSERS)}".strip()


def generate_legit(n: int, seed: int) -> list[str | None]:
    rng = np.random.default_rng(seed)
    return [legit_message(rng) for _ in range(n)]


def main():
    for name, seed in (("legit_calibration", 22), ("legit_test", 23)):
        path = f"data/similarity/{name}.json"
        with open(path, "w") as f:
            json.dump(generate_legit(1000, seed), f, indent=0)
        print(f"Wrote 1000 rows -> {path}")


if __name__ == "__main__":
    main()
