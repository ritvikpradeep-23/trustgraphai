"""Fingerprint matching against a database of known fakes (images and video
frames).

A fingerprint is a perceptual hash. Unlike SHA/MD5 it survives the
recompression and resizing that WhatsApp, Instagram and other apps apply, so
a re-shared copy of a known fake still matches. The match is returned NEXT TO
any model answer, never blended into it: it only catches content that is
already in the database. (Text is matched against reported scams by
/api/detect, app/services/previous_report_matcher.py.)
"""
