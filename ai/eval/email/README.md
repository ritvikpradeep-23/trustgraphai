# Email scam data (real, public)

`python scripts/import_email_datasets.py` builds the email sets; `python eval/email/check.py` scores them.

Source: **Phishing Email Curated Datasets**, Zenodo record 8339691 (DOI 10.5281/zenodo.8339691),
licensed CC BY 4.0. Downloaded from the byte-identical Hugging Face mirror
`kudzaiprichard/aura-phishing-email-corpus` (revision `539567cee21d03c83bd2fb1b142c18a80904eb72`).
Files used, with the MD5s Zenodo publishes:

| File | Contents | MD5 |
|---|---|---|
| `Nazario_5.csv` | 1,565 phishing emails (Jose Nazario's corpus) + 1,500 honest | `45db8330ea4aabbf72f5199949ae03e5` |
| `Nigerian_5.csv` | 3,332 advance-fee fraud emails + 2,999 honest | `edfbbb89c40e7447f47867bcc82e72f9` |

Changes made: subject and body joined, cut to 1,000 characters, links replaced by `link.invalid`,
email addresses by `[email]`, long digit runs by `[number]`, near-duplicates dropped. Labels are the
dataset's own and are not individually verified: a few "phishing" rows are other scam types.

The raw files and the design / held-out sets stay in `eval/external/email/` (gitignored). The
learning routine added 146 of the scam emails it missed and 31 honest emails it flagged to
`models/similarity_corpus.json`; those are redistributed under CC BY 4.0 with this attribution.
