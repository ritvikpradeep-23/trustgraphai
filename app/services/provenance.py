import binascii
from io import BytesIO
import mimetypes
import os
import re
import struct
import tempfile
import zipfile
import zlib
from pathlib import PurePosixPath
from typing import BinaryIO
from xml.etree import ElementTree

from app.schemas.provenance import ProvenanceMetadata, ProvenanceResponse


MAX_ANALYSIS_BYTES = 50 * 1024 * 1024
C2PA_MANIFEST_STORE_UUID = bytes.fromhex("6332706100110010800000aa00389b71")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class MalformedFileError(ValueError):
    pass


class UnsupportedFileError(ValueError):
    pass


def _safe_filename(filename: str | None) -> str | None:
    if not filename:
        return None
    cleaned = filename.replace("\\", "/")
    return PurePosixPath(cleaned).name or None


def _detect_content_type(data: bytes, filename: str | None) -> str | None:
    if data.startswith(PNG_SIGNATURE):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        return "video/quicktime" if brand in (b"qt  ",) else "video/mp4"
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "audio/wav"
    if data.startswith(b"ID3") or (len(data) >= 2 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0):
        return "audio/mpeg"
    if data.startswith(b"fLaC"):
        return "audio/flac"
    if data.startswith(b"OggS"):
        return "audio/ogg"
    if data.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                names = set(archive.namelist())
            if "word/document.xml" in names:
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if "ppt/presentation.xml" in names:
                return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            if "xl/workbook.xml" in names:
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return "application/zip"
        except (OSError, zipfile.BadZipFile):
            raise MalformedFileError("Invalid ZIP container")
    guessed, _encoding = mimetypes.guess_type(filename or "")
    if guessed and guessed.startswith("text/"):
        try:
            data.decode("utf-8")
            return guessed
        except UnicodeDecodeError:
            return None
    return None


def _put_tag(tags: dict[str, str], key: str, value: bytes | str) -> None:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    value = value.strip("\x00 \t\r\n")
    if not value:
        return
    normalized = key.casefold().replace("_", "").replace(" ", "")
    if normalized in {"software", "creatortool", "lastmodifiedby"}:
        tags["software"] = value[:512]
    elif normalized in {"producer"}:
        tags["producer"] = value[:512]
    elif normalized in {"creationdate", "creationtime", "created", "createdate", "datetimeoriginal"}:
        tags["created_at"] = value[:128]
    elif normalized in {"moddate", "modified", "modifydate", "modificationtime", "datetimemodified"}:
        tags["modified_at"] = value[:128]
    elif normalized in {"author", "description", "copyright", "title"}:
        tags[key[:64]] = value[:512]


def _png_tags(data: bytes) -> dict[str, str]:
    tags: dict[str, str] = {}
    offset = len(PNG_SIGNATURE)
    found_iend = False
    found_ihdr = False
    found_idat = False
    inflater = zlib.decompressobj()
    expanded_bytes = 0
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        end = offset + 12 + length
        if length > MAX_ANALYSIS_BYTES or end > len(data):
            raise MalformedFileError("Truncated PNG chunk")
        chunk_type = data[offset + 4 : offset + 8]
        chunk_data = data[offset + 8 : offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length : end])[0]
        actual_crc = binascii.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
        if expected_crc != actual_crc:
            raise MalformedFileError("Invalid PNG chunk checksum")
        if not found_ihdr:
            if chunk_type != b"IHDR" or length != 13:
                raise MalformedFileError("Invalid PNG header")
            width, height = struct.unpack(">II", chunk_data[:8])
            if width == 0 or height == 0:
                raise MalformedFileError("Invalid PNG dimensions")
            found_ihdr = True
            found_ihdr = True
        elif chunk_type == b"IHDR":
            raise MalformedFileError("Duplicate PNG header")
        if chunk_type == b"tEXt" and b"\x00" in chunk_data:
            key, value = chunk_data.split(b"\x00", 1)
            _put_tag(tags, key.decode("latin-1", errors="replace"), value)
        if chunk_type == b"IDAT":
            found_idat = True
            remaining_limit = MAX_ANALYSIS_BYTES + 1 - expanded_bytes
            decoded = inflater.decompress(chunk_data, remaining_limit)
            expanded_bytes += len(decoded)
            if expanded_bytes > MAX_ANALYSIS_BYTES or inflater.unconsumed_tail:
                raise MalformedFileError("PNG image data exceeds the analysis limit")
        if chunk_type == b"IEND":
            found_iend = True
            break
        offset = end
    if not found_ihdr or not found_idat or not found_iend:
        raise MalformedFileError("PNG end marker missing")
    expanded_bytes += len(inflater.flush(MAX_ANALYSIS_BYTES + 1 - expanded_bytes))
    if expanded_bytes > MAX_ANALYSIS_BYTES or not inflater.eof:
        raise MalformedFileError("Invalid PNG image data")
    return tags


def _pdf_tags(data: bytes) -> dict[str, str]:
    if b"%%EOF" not in data[-2048:]:
        raise MalformedFileError("PDF end marker missing")
    tags: dict[str, str] = {}
    for key, normalized in ((b"CreationDate", "CreationDate"), (b"ModDate", "ModDate"), (b"Producer", "Producer"), (b"Creator", "Creator")):
        match = re.search(rb"/" + key + rb"\s*\(([^()]{1,512})\)", data)
        if match:
            _put_tag(tags, normalized, match.group(1).replace(b"\\(", b"(").replace(b"\\)", b")"))
    return tags


def _jpeg_tags(data: bytes) -> dict[str, str]:
    if not data.endswith(b"\xff\xd9"):
        raise MalformedFileError("JPEG end marker missing")
    tags: dict[str, str] = {}
    # Read only recognized XMP properties; do not claim to validate XMP or EXIF.
    for property_name, normalized in (
        (rb"(?:xmp:)?CreatorTool", "CreatorTool"),
        (rb"(?:xmp:)?CreateDate", "CreateDate"),
        (rb"(?:xmp:)?ModifyDate", "ModifyDate"),
    ):
        match = re.search(property_name + rb"\s*=\s*[\"']([^\"']{1,512})[\"']", data)
        if match:
            _put_tag(tags, normalized, match.group(1))
    return tags


def _c2pa_manifest_store_detected(data: bytes) -> bool:
    """Look for the C2PA label and store UUID together in a JUMBF description box."""
    offset = 0
    while True:
        type_offset = data.find(b"jumb", offset)
        if type_offset < 4:
            return False
        box_start = type_offset - 4
        box_size = struct.unpack(">I", data[box_start:type_offset])[0]
        box_end = box_start + box_size
        if box_size < 16 or box_end > len(data):
            offset = type_offset + 4
            continue

        child_offset = type_offset + 4
        while child_offset + 8 <= box_end:
            child_size = struct.unpack(">I", data[child_offset : child_offset + 4])[0]
            child_type = data[child_offset + 4 : child_offset + 8]
            if child_size < 8 or child_offset + child_size > box_end:
                break
            if child_type == b"jumd":
                description = data[child_offset + 8 : child_offset + child_size]
                if C2PA_MANIFEST_STORE_UUID in description and b"c2pa\x00" in description:
                    return True
            child_offset += child_size
        offset = type_offset + 4


def _docx_tags(path: str) -> dict[str, str]:
    tags: dict[str, str] = {}
    try:
        with zipfile.ZipFile(path) as archive:
            if "word/document.xml" not in archive.namelist():
                return tags
            if "docProps/core.xml" not in archive.namelist():
                return tags
            info = archive.getinfo("docProps/core.xml")
            if info.file_size > 1024 * 1024:
                return tags
            root = ElementTree.fromstring(archive.read(info))
    except (OSError, zipfile.BadZipFile, ElementTree.ParseError, KeyError):
        return tags
    for element in root.iter():
        key = element.tag.rsplit("}", 1)[-1]
        if element.text:
            _put_tag(tags, key, element.text)
    return tags


def _unavailable(
    filename: str | None,
    supplied_content_type: str | None,
    warning: str,
    *,
    size_bytes: int | None = None,
    content_type: str | None = None,
) -> ProvenanceResponse:
    return ProvenanceResponse(
        available=False,
        provenance_present=None,
        c2pa_present=None,
        c2pa_verified=None,
        metadata=ProvenanceMetadata(
            filename=filename,
            size_bytes=size_bytes,
            supplied_content_type=supplied_content_type,
            content_type=content_type,
        ),
        signals={"mime_type_detected": content_type is not None, "metadata_present": None, "c2pa_marker_detected": None},
        warnings=[warning],
    )


def analyze_provenance(
    stream: BinaryIO,
    *,
    filename: str | None,
    supplied_content_type: str | None,
) -> ProvenanceResponse:
    safe_name = _safe_filename(filename)
    temp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix="trustgraph-provenance-", suffix=".upload", delete=False) as temp:
            temp_path = temp.name
            size_bytes = 0
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                if not isinstance(chunk, bytes):
                    raise OSError("Uploaded content is not a binary stream")
                size_bytes += len(chunk)
                if size_bytes > MAX_ANALYSIS_BYTES:
                    return _unavailable(
                        safe_name,
                        supplied_content_type,
                        "File exceeds the provenance analysis size limit.",
                    )
                temp.write(chunk)

        with open(temp_path, "rb") as file:
            data = file.read(MAX_ANALYSIS_BYTES + 1)
        content_type = _detect_content_type(data, safe_name)
        if content_type is None:
            return _unavailable(
                safe_name,
                supplied_content_type,
                "File format is unsupported; embedded provenance could not be determined.",
                size_bytes=size_bytes,
            )

        if content_type == "image/png":
            tags = _png_tags(data)
        elif content_type == "image/jpeg":
            tags = _jpeg_tags(data)
        elif content_type == "application/pdf":
            tags = _pdf_tags(data)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            tags = _docx_tags(temp_path)
        else:
            tags = {}

        c2pa_present = _c2pa_manifest_store_detected(data)
        provenance_present = bool(tags) or c2pa_present
        warnings = [
            "C2PA detection checks the embedded JUMBF manifest-store identifier; cryptographic verification is unavailable."
        ]
        if supplied_content_type and supplied_content_type != content_type:
            warnings.append("Supplied content type differs from the type detected from the file signature.")
        if c2pa_present:
            warnings.append("A C2PA manifest-store identifier was detected; this is not a verification result.")
        else:
            warnings.append("No C2PA manifest-store identifier was detected; missing provenance is not an authenticity verdict.")

        return ProvenanceResponse(
            available=True,
            provenance_present=provenance_present,
            c2pa_present=c2pa_present,
            c2pa_verified=None,
            metadata=ProvenanceMetadata(
                filename=safe_name,
                size_bytes=size_bytes,
                supplied_content_type=supplied_content_type,
                content_type=content_type,
                created_at=tags.get("created_at"),
                modified_at=tags.get("modified_at"),
                software=tags.get("software"),
                producer=tags.get("producer"),
                embedded={key: value for key, value in tags.items() if key not in {"created_at", "modified_at", "software", "producer"}},
            ),
            signals={
                "mime_type_detected": True,
                "metadata_present": bool(tags),
                "c2pa_marker_detected": c2pa_present,
            },
            warnings=warnings,
        )
    except MalformedFileError:
        return _unavailable(
            safe_name,
            supplied_content_type,
            "File is malformed or truncated; embedded metadata and provenance could not be determined.",
        )
    except Exception:
        return _unavailable(
            safe_name,
            supplied_content_type,
            "File could not be read safely; embedded metadata and provenance could not be determined.",
        )
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
            except OSError:
                pass
