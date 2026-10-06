# Phase 0: training data check

> The data is synthetic (written by the generator in `eval/`). Nothing here is real-world accuracy.

**All prerequisites are present. No problems found.**

## Prerequisites

- All 11 required fields present on every corpus and dev row: id, text, label, category, split, template_family, channel, language, evasion_type, novelty, source.
- Frozen test set hash verified: `6fc6fd2858a5bb33…` (generator seed 0).
- 512 template families; none crosses splits.
- Training-data hashes: corpus `4c2ed0bec636e478…`, dev `f60440ee53add519…`.

| Split | Scams (known types) | Scams (types the engine had no examples for) | Honest | Scam types |
|---|---|---|---|---|
| corpus | 304 | 351 | 758 | 29 |
| dev | 205 | 247 | 1498 | 29 |

The corpus split holds all 29 scam types, so once a model trains on it the evaluation's "never seen" types are no longer unseen. Novelty is measured by leave-one-type-out and by versions trained on the 13 known types only.

## Shortcut check (corpus + dev; flagged if a group of 10+ is over 85% one label)

| Group | Value | Messages | Share that are scams | Shortcut risk |
|---|---|---|---|---|
| language | en | 2963 | 31% |  |
| language | hinglish | 228 | 56% |  |
| language | manglish | 172 | 40% |  |
| channel | email | 530 | 31% |  |
| channel | instagram | 363 | 36% |  |
| channel | messenger | 317 | 32% |  |
| channel | sms | 1005 | 32% |  |
| channel | whatsapp | 1148 | 34% |  |
| evasion_type | casual_lowercase | 166 | 0% | **yes** |
| evasion_type | emoji_padding | 267 | 27% |  |
| evasion_type | leetspeak | 73 | 100% | **yes** |
| evasion_type | none | 2657 | 29% |  |
| evasion_type | obfuscated_link | 69 | 100% | **yes** |
| evasion_type | spacing | 73 | 100% | **yes** |
| evasion_type | split_phrasing | 58 | 100% | **yes** |
| length | long (30+) | 72 | 99% | **yes** |
| length | medium (15-29) | 1851 | 48% |  |
| length | short (<15 words) | 1440 | 10% | **yes** |
| link | [LINK] placeholder | 130 | 32% |  |
| link | no link | 2778 | 31% |  |
| link | reserved-domain, other | 260 | 4% | **yes** |
| link | reserved-domain, scam style | 195 | 100% | **yes** |
| has [PHONE] | no | 3322 | 32% |  |
| has [PHONE] | yes | 41 | 100% | **yes** |
| has 'Details:' suffix | no | 3053 | 36% |  |
| has 'Details:' suffix | yes | 310 | 0% | **yes** |
| has an INV- code | no | 3275 | 33% |  |
| has an INV- code | yes | 88 | 12% | **yes** |

12 flagged group(s). Every one is a way a model could tell the labels apart without learning anything about scams. How each is handled is in the Phase 0 notes below.

## Phase 0 notes: how each shortcut is handled

| Shortcut | Why it exists | Handling |
|---|---|---|
| Evasion tricks (leetspeak, spaced letters, obfuscated links, split lines) appear only in scams; all-lowercase only in honest messages | The generator applies scam tricks only to scams | Text is normalized before Tracks B and C see it: lowercased, spaced letters rejoined, leetspeak digits inside words undone, '[.]'/' dot '/'hxxp' links decoded. A trick then looks like the plain message. |
| Link style: '.test', '.invalid', 'secure-pay.example.com' only in scams; 'app.example.com' only in honest | The generator draws scam and honest links from different patterns | Every link becomes one `<link>` token in both classes. |
| 'Details: <link>' suffix only in honest messages | Generator habit | Link becomes `<link>`; the word 'details' is on the audit's watch list and is removed in the audit retrain. |
| [PHONE] only in scams | Only scam templates mention a number to call | Phone numbers and [PHONE] become one `<phone>` token; on the audit watch list. |
| INV- codes mostly in honest code messages | A known generator slip | 'INV-12345' and digit runs become `<num>`. |
| Length: 30+ words is 99% scams, under 15 words 90% honest | Partly real (scams explain more), mostly the generator | Can't be removed without new data. Reported by length bucket, and the classifier must clearly beat a baseline that only knows length and whether there is a link. |

Language, channel and the [LINK] placeholder are balanced (no flag).
