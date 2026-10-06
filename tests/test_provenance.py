import binascii
import os
import struct
import tempfile
import unittest
import zlib
from io import BytesIO
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.provenance import C2PA_MANIFEST_STORE_UUID, analyze_provenance


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = binascii.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def make_png(*text_tags: tuple[str, str], extra: bytes = b"") -> bytes:
    header = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    parts = [PNG_SIGNATURE, png_chunk(b"IHDR", header)]
    for key, value in text_tags:
        parts.append(png_chunk(b"tEXt", key.encode("latin-1") + b"\x00" + value.encode("latin-1")))
    if extra:
        parts.append(png_chunk(b"caBX", extra))
    parts.extend((png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00")), png_chunk(b"IEND", b"")))
    return b"".join(parts)


class ProvenanceServiceTests(unittest.TestCase):
    def analyze(self, payload: bytes, filename: str = "sample.png"):
        return analyze_provenance(
            BytesIO(payload), filename=filename, supplied_content_type="image/png"
        )

    def test_valid_supported_file_reports_detected_mime(self):
        result = self.analyze(make_png())

        self.assertTrue(result.available)
        self.assertEqual(result.metadata.content_type, "image/png")
        self.assertEqual(result.metadata.size_bytes, len(make_png()))
        self.assertFalse(result.provenance_present)

    def test_no_provenance_is_not_an_authenticity_verdict(self):
        result = self.analyze(make_png())

        self.assertFalse(result.provenance_present)
        self.assertFalse(result.c2pa_present)
        self.assertIsNone(result.c2pa_verified)
        self.assertTrue(any("not an authenticity verdict" in warning for warning in result.warnings))

    def test_embedded_metadata_is_extracted(self):
        result = self.analyze(
            make_png(("Software", "Example Editor"), ("Creation Time", "2024-01-02T03:04:05Z"))
        )

        self.assertTrue(result.provenance_present)
        self.assertTrue(result.signals["metadata_present"])
        self.assertEqual(result.metadata.software, "Example Editor")
        self.assertEqual(result.metadata.created_at, "2024-01-02T03:04:05Z")

    def test_malformed_known_file_is_unavailable(self):
        result = self.analyze(PNG_SIGNATURE + b"truncated")

        self.assertFalse(result.available)
        self.assertIsNone(result.provenance_present)
        self.assertIsNone(result.c2pa_present)
        self.assertIsNone(result.c2pa_verified)
        self.assertIn("malformed", result.warnings[0])

    def test_unsupported_file_is_unavailable(self):
        result = self.analyze(b"not a supported media format", "unknown.bin")

        self.assertFalse(result.available)
        self.assertIsNone(result.c2pa_present)
        self.assertEqual(result.metadata.filename, "unknown.bin")

    def test_c2pa_identifier_is_detected_but_never_claimed_verified(self):
        description = (
            b"\x00\x00\x00\x00\x03c2pa\x00" + C2PA_MANIFEST_STORE_UUID
        )
        description_box = struct.pack(">I4s", 8 + len(description), b"jumd") + description
        manifest_store = struct.pack(">I4s", 8 + len(description_box), b"jumb") + description_box
        result = self.analyze(make_png(extra=manifest_store))

        self.assertTrue(result.c2pa_present)
        self.assertTrue(result.provenance_present)
        self.assertIsNone(result.c2pa_verified)

    def test_uuid_outside_a_jumbf_description_is_not_called_c2pa(self):
        result = self.analyze(make_png(extra=C2PA_MANIFEST_STORE_UUID))

        self.assertFalse(result.c2pa_present)
        self.assertIsNone(result.c2pa_verified)

    def test_temporary_file_is_removed_after_analysis(self):
        original = tempfile.NamedTemporaryFile
        temp_paths = []

        def track_temp(*args, **kwargs):
            created = original(*args, **kwargs)
            temp_paths.append(created.name)
            return created

        with patch("app.services.provenance.tempfile.NamedTemporaryFile", side_effect=track_temp):
            result = self.analyze(make_png())

        self.assertTrue(result.available)
        self.assertEqual(len(temp_paths), 1)
        self.assertFalse(os.path.exists(temp_paths[0]))

    def test_unreadable_upload_returns_unavailable_and_cleans_temp_file(self):
        original = tempfile.NamedTemporaryFile
        temp_paths = []

        def track_temp(*args, **kwargs):
            created = original(*args, **kwargs)
            temp_paths.append(created.name)
            return created

        class UnreadableStream:
            def read(self, _size):
                raise OSError("read failed")

        with patch("app.services.provenance.tempfile.NamedTemporaryFile", side_effect=track_temp):
            result = analyze_provenance(
                UnreadableStream(), filename="sample.png", supplied_content_type="image/png"
            )

        self.assertFalse(result.available)
        self.assertIsNone(result.c2pa_verified)
        self.assertEqual(len(temp_paths), 1)
        self.assertFalse(os.path.exists(temp_paths[0]))


class ProvenanceEndpointTests(unittest.TestCase):
    def test_api_response_and_safe_filename(self):
        client = TestClient(app)
        response = client.post(
            "/api/provenance/analyze",
            files={
                "file": (
                    r"C:\private\sample.png",
                    make_png(("Software", "Test Producer")),
                    "image/png",
                )
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["available"])
        self.assertTrue(result["provenance_present"])
        self.assertIsNone(result["c2pa_verified"])
        self.assertEqual(result["metadata"]["filename"], "sample.png")
        self.assertNotIn("private", str(result))
        self.assertIn("signals", result)
        self.assertIn("warnings", result)


if __name__ == "__main__":
    unittest.main()
