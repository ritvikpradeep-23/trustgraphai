# Proposed red-flag rules (NOT applied, waiting for your OK)

> Synthetic data except the real-SMS column. Counts, not real-world accuracy.

Drafted after reading the 221 scams missed in rounds 03-12 (`reports/fast/round_*.md`). Each rule targets one general giveaway, not one message. All of them go through the existing negation guard, so a warning like "never share your recovery phrase" doesn't count. **None is in the engine:** the round runs and the final test used the engine without them.

| Rule | Giveaway | Weight | Missed scams it would catch (rounds 03-12, in-sample) | Dev scams it hits (of 120) | Dev honest hit (of 240) | Round honest hit (of 1,200) | Real UK SMS honest hit (of 4,827) |
|---|---|---|---|---|---|---|---|
| A | asks for a PIN or approval to RECEIVE money | 0.7 | 17 | 4 | 0 | 0 | 0 |
| B | asks you to run a command or script it copied for you | 0.8 | 5 | 0 | 0 | 0 | 0 |
| C | asks to connect a wallet or share a recovery phrase | 0.7 | 5 | 0 | 0 | 0 | 0 |
| D | tells you to stay on a video call ("digital arrest") | 0.7 | 7 | 0 | 0 | 0 | 0 |
| E | threatens to contact your contacts, family or employer | 0.6 | 5 | 4 | 0 | 0 | 0 |
| F | asks you to pay to unlock, release or withdraw something | 0.5 | 7 | 0 | 0 | 0 | 0 |
| G | threatens to cut a service or block an account today | 0.4 | 2 | 5 | 0 | 0 | 0 |
| H | asks for a deposit or advance to hold a rental or booking | 0.4 | 7 | 1 | 0 | 0 | 0 |

**How to read this:**
- The "missed scams" column is in-sample: I wrote the rules while looking at those messages, so it flatters them.
  The dev column is fairer. None of the rules was written from dev messages.
- **Zero honest hits everywhere**, including 4,827 real UK texts. They're narrow by design.
- **What no rule should catch:** the deliberately soft scams with no ask ("you were added to our investor learning
  group", "are you free? need something done discreetly", "good morning sweetheart"). They read exactly like honest
  messages; only who sent them (continuity, precedent) can tell them apart.
- **Hinglish/Manglish misses** (e.g. QR and electricity messages in Manglish) are only partly covered: rule A
  includes "aa jayenge" / "varum" ("will come"), the rest is English wording.

## The diff, to add to `RED_FLAGS` in `src/trustgraph/similarity/detector.py`

```python
    # Proposed rule A
    (0.7, "asks for a PIN or approval to RECEIVE money",
     r"\\b(scan|approve|accept|enter|type)\\b.{0,60}\\b(upi )?pin\\b.{0,60}\\b(receive|get|credit|refund|come back|aa jayenge|varum)\\b|\\bapprove\\b.{0,30}\\b(the |this |my )?(incoming |payment |collect |upi )?request\\b.{0,60}\\b(receive|credit|refund|get it|back|reverse)"),
    # Proposed rule B
    (0.8, "asks you to run a command or script it copied for you",
     r"\\b(run|paste|execute)\\b.{0,50}\\b(command|script|code|fix)\\b.{0,50}\\b(copied|clipboard)\\b|\\b(copied|clipboard)\\b.{0,50}\\b(command|script|code)\\b.{0,40}\\b(run|paste|execute)\\b"),
    # Proposed rule C
    (0.7, "asks to connect a wallet or share a recovery phrase",
     r"\\b(connect|link)\\b (your )?wallet\\b|\\b(recovery|seed) (phrase|words)\\b|\\bprivate key\\b"),
    # Proposed rule D
    (0.7, "tells you to stay on a video call (\"digital arrest\")",
     r"\\b(stay|remain|keep)\\b (on )?(this|the) (video )?call\\b|\\bdo not (disconnect|cut|end) (the )?(video )?call\\b|\\bkeep (the|your) (camera|video) on\\b|\\bdigital arrest\\b"),
    # Proposed rule E
    (0.6, "threatens to contact your contacts, family or employer",
     r"\\b(message|call|send|share|post)\\b.{0,30}\\b(all |everyone in )?(your|ur) (contacts|contact list|family|employer|photos)\\b.{0,40}|(\\bor\\b|\\bunless\\b|\\botherwise\\b).{0,30}\\b(message|call|contact)\\b.{0,20}\\b(your )?(contacts|family|employer)\\b"),
    # Proposed rule F
    (0.5, "asks you to pay to unlock, release or withdraw something",
     r"\\b(pay|deposit|recharge|transfer)\\b.{0,50}\\bto (unlock|release|restore|withdraw|reactivate)\\b"),
    # Proposed rule G
    (0.4, "threatens to cut a service or block an account today",
     r"\\b(power|electricity|current|supply|account|sim|tag|fastag|licen[cs]e)\\b.{0,40}\\b(cut|disconnected|suspended|blocked|blacklisted|deactivated|frozen)\\b.{0,40}\\b(today|tonight|within \\d+ hours|immediately|in \\d+ hours)\\b"),
    # Proposed rule H
    (0.4, "asks for a deposit or advance to hold a rental or booking",
     r"\\b(deposit|token advance|holding fee|advance)\\b.{0,60}\\b(hold|block|reserve|secure|confirm)\\b.{0,40}\\b(flat|room|apartment|villa|studio|pg|booking|it)\\b|\\b(hold|block|reserve)\\b.{0,30}\\b(flat|room|apartment)\\b.{0,60}\\b(deposit|advance)\\b"),
```

If approved, apply it as its own change, run the gate (`python -m pytest tests/`, the 24 demo scenarios, dev recall and real-SMS check), and note in the summary that the final test (rounds 13-14) was scored **before** these rules, so their effect on it is unmeasured unless a new test set is made.
