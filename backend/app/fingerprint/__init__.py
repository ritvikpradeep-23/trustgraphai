"""Fingerprint matching against a database of known fakes.

A fingerprint is a perceptual hash (images and video frames) or a SimHash
(text). Unlike SHA/MD5, these survive the recompression and resizing that
WhatsApp, Instagram and other apps apply, so a re-shared copy of a known fake
still matches. The match is returned NEXT TO the model's score, never blended
into it: it only catches content that is already in the database.
"""
