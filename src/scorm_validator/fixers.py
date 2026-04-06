"""Auto-fix common SCORM package issues.

Operates on the manifest XML in-memory, then rewrites the zip with
the corrected manifest. Non-destructive: writes to a new output path.
"""

import shutil
import zipfile

from lxml import etree

from scorm_validator.models import NS_TO_VERSION


def fix_package(input_path: str, output_path: str) -> list[str]:
    """Apply all available fixes and write corrected package to output_path.

    Returns a list of human-readable descriptions of fixes applied.
    """
    fixes_applied = []

    with zipfile.ZipFile(input_path, "r") as zf_in:
        if "imsmanifest.xml" not in zf_in.namelist():
            raise ValueError("Cannot fix: imsmanifest.xml not found in package")

        xml_bytes = zf_in.read("imsmanifest.xml")

        xml_bytes, bom_fix = _fix_bom(xml_bytes)
        if bom_fix:
            fixes_applied.append(bom_fix)

        xml_bytes, encoding_fix = _fix_encoding_declaration(xml_bytes)
        if encoding_fix:
            fixes_applied.append(encoding_fix)

        try:
            root = etree.fromstring(xml_bytes)
        except etree.XMLSyntaxError:
            # can't fix what we can't parse
            shutil.copy2(input_path, output_path)
            return ["XML is malformed — copied without changes"]

        ns_uri = _get_root_namespace(root)
        ns = {"cp": ns_uri} if ns_uri else {}

        metadata_fix = _fix_missing_metadata(root, ns, ns_uri)
        if metadata_fix:
            fixes_applied.append(metadata_fix)

        desc_fix = _fix_missing_description(root, ns, ns_uri)
        if desc_fix:
            fixes_applied.append(desc_fix)

        fixed_xml = etree.tostring(root, xml_declaration=True, encoding="UTF-8")

        # TODO: add fix for duplicate resource identifiers
        _write_fixed_zip(zf_in, fixed_xml, output_path)

    return fixes_applied


def _fix_bom(xml_bytes: bytes) -> tuple[bytes, str | None]:
    if xml_bytes.startswith(b"\xef\xbb\xbf"):
        return xml_bytes[3:], "Stripped UTF-8 BOM from manifest"
    return xml_bytes, None


def _fix_encoding_declaration(xml_bytes: bytes) -> tuple[bytes, str | None]:
    """Fix encoding declaration if it doesn't match actual encoding."""
    # only handle the common case: declared as latin-1 but actually utf-8
    if b'encoding="iso-8859-1"' in xml_bytes[:100].lower() or \
       b"encoding='iso-8859-1'" in xml_bytes[:100].lower():
        try:
            xml_bytes.decode("utf-8")
            fixed = xml_bytes.replace(
                b'encoding="iso-8859-1"', b'encoding="UTF-8"'
            ).replace(
                b"encoding='iso-8859-1'", b"encoding='UTF-8'"
            )
            return fixed, "Fixed encoding declaration (iso-8859-1 -> UTF-8)"
        except UnicodeDecodeError:
            pass
    return xml_bytes, None


def _get_root_namespace(root: etree._Element) -> str | None:
    tag = root.tag
    if tag.startswith("{"):
        return tag.split("}")[0][1:]
    return None


def _fix_missing_metadata(
    root: etree._Element, ns: dict, ns_uri: str | None
) -> str | None:
    if not ns:
        return None

    meta = root.find("cp:metadata", ns)
    if meta is not None:
        return None

    # detect version from namespace to insert correct schemaversion
    version_family = NS_TO_VERSION.get(ns_uri, "1.2")
    schema_version = "1.2" if version_family == "1.2" else "2004 4th Edition"

    meta = etree.SubElement(root, f"{{{ns_uri}}}metadata")
    schema = etree.SubElement(meta, f"{{{ns_uri}}}schema")
    schema.text = "ADL SCORM"
    sv = etree.SubElement(meta, f"{{{ns_uri}}}schemaversion")
    sv.text = schema_version

    # insert metadata as first child of manifest
    root.remove(meta)
    root.insert(0, meta)

    return f"Inserted missing <metadata> with schemaversion={schema_version}"


def _fix_missing_description(
    root: etree._Element, ns: dict, ns_uri: str | None
) -> str | None:
    if not ns:
        return None

    meta = root.find("cp:metadata", ns)
    if meta is None:
        return None

    desc = meta.find("cp:description", ns)
    if desc is not None:
        return None

    desc = etree.SubElement(meta, f"{{{ns_uri}}}description")
    desc.text = ""
    return "Added empty <description> element to metadata"


def _write_fixed_zip(
    original_zf: zipfile.ZipFile, fixed_xml: bytes, output_path: str
):
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf_out:
        for item in original_zf.infolist():
            if item.filename == "imsmanifest.xml":
                zf_out.writestr(item, fixed_xml)
            else:
                zf_out.writestr(item, original_zf.read(item.filename))
